# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""Assemble function for converting a list of circuits into a qobj"""
import copy
import uuid

import numpy
import sympy

from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.pulse import ConditionedSchedule, UserLoDict
from qiskit.pulse.commands import DriveInstruction
from qiskit.qobj import (QasmQobj, PulseQobj, QobjExperimentHeader, QobjHeader,
                         QasmQobjInstruction, QasmQobjExperimentConfig, QasmQobjExperiment,
                         QasmQobjConfig, QobjConditional,
                         PulseQobjInstruction, PulseQobjExperimentConfig, PulseQobjExperiment,
                         PulseQobjConfig, QobjPulseLibrary)
from .pulse_to_qobj import SuperConverter
from .run_config import RunConfig


def assemble_circuits(circuits, run_config=None, qobj_header=None, qobj_id=None):
    """Assembles a list of circuits into a qobj which can be run on the backend.

    Args:
        circuits (list[QuantumCircuits] or QuantumCircuit): circuits to assemble
        run_config (RunConfig): RunConfig object
        qobj_header (QobjHeader): header to pass to the results
        qobj_id (int): identifier for the generated qobj

    Returns:
        QasmQobj: the Qobj to be run on the backends
    """
    qobj_header = qobj_header or QobjHeader()
    run_config = run_config or RunConfig()
    if isinstance(circuits, QuantumCircuit):
        circuits = [circuits]

    userconfig = QasmQobjConfig(**run_config.to_dict())
    experiments = []
    max_n_qubits = 0
    max_memory_slots = 0
    for circuit in circuits:
        # header stuff
        n_qubits = 0
        memory_slots = 0
        qubit_labels = []
        clbit_labels = []

        qreg_sizes = []
        creg_sizes = []
        for qreg in circuit.qregs:
            qreg_sizes.append([qreg.name, qreg.size])
            for j in range(qreg.size):
                qubit_labels.append([qreg.name, j])
            n_qubits += qreg.size
        for creg in circuit.cregs:
            creg_sizes.append([creg.name, creg.size])
            for j in range(creg.size):
                clbit_labels.append([creg.name, j])
            memory_slots += creg.size

        # TODO: why do we need creq_sizes and qreg_sizes in header
        # TODO: we need to rethink memory_slots as they are tied to classical bit
        experimentheader = QobjExperimentHeader(qubit_labels=qubit_labels,
                                                n_qubits=n_qubits,
                                                qreg_sizes=qreg_sizes,
                                                clbit_labels=clbit_labels,
                                                memory_slots=memory_slots,
                                                creg_sizes=creg_sizes,
                                                name=circuit.name)
        # TODO: why do we need n_qubits and memory_slots in both the header and the config
        experimentconfig = QasmQobjExperimentConfig(n_qubits=n_qubits, memory_slots=memory_slots)

        instructions = []
        for op_context in circuit.data:
            op = op_context[0]
            qargs = op_context[1]
            cargs = op_context[2]
            current_instruction = QasmQobjInstruction(name=op.name)
            if qargs:
                qubit_indices = [qubit_labels.index([qubit[0].name, qubit[1]])
                                 for qubit in qargs]
                current_instruction.qubits = qubit_indices
            if cargs:
                clbit_indices = [clbit_labels.index([clbit[0].name, clbit[1]])
                                 for clbit in cargs]
                current_instruction.memory = clbit_indices

            if op.params:
                params = list(map(lambda x: x.evalf(), op.params))
                params = [sympy.matrix2numpy(x, dtype=complex)
                          if isinstance(x, sympy.Matrix) else x for x in params]
                if len(params) == 1 and isinstance(params[0], numpy.ndarray):
                    # TODO: Aer expects list of rows for unitary instruction params;
                    # change to matrix in Aer.
                    params = params[0]
                current_instruction.params = params
            # TODO: I really dont like this for snapshot. I also think we should change
            # type to snap_type
            if op.name == "snapshot":
                current_instruction.label = str(op.params[0])
                current_instruction.type = str(op.params[1])
            if op.name == 'unitary':
                if op._label:
                    current_instruction.label = op._label
            if op.control:
                mask = 0
                for clbit in clbit_labels:
                    if clbit[0] == op.control[0].name:
                        mask |= (1 << clbit_labels.index(clbit))

                current_instruction.conditional = QobjConditional(mask="0x%X" % mask,
                                                                  type='equals',
                                                                  val="0x%X" % op.control[1])

            instructions.append(current_instruction)
        experiments.append(QasmQobjExperiment(instructions=instructions, header=experimentheader,
                                              config=experimentconfig))
        if n_qubits > max_n_qubits:
            max_n_qubits = n_qubits
        if memory_slots > max_memory_slots:
            max_memory_slots = memory_slots

    userconfig.memory_slots = max_memory_slots
    userconfig.n_qubits = max_n_qubits

    return QasmQobj(qobj_id=qobj_id or str(uuid.uuid4()), config=userconfig,
                    experiments=experiments, header=qobj_header)


def _replaced_with_user_los(user_lo_dict, default_los):
    """Return user LO frequencies replaced from `default_los`.
    Args:
        user_lo_dict(UserLoDict): dictionary of user's LO frequencies
        default_los(list(float)): default LO frequencies to be replaced
    Returns:
        List: user LO frequencies
    """
    res = copy.copy(default_los)
    for channel, user_lo in user_lo_dict.items():
        res[channel.index] = user_lo

    return res


def assemble_schedules(schedules, dict_config, dict_header, ):
    """Assembles a list of circuits into a qobj which can be run on the backend.

    Args:
        schedules (list[ConditionedSchedule] or ConditionedSchedule): schedules to assemble
        dict_config (dict): configuration of experiments
        dict_header (dict): header to pass to the results

    Returns:
        PulseQobj: the Qobj to be run on the backends

    Raises:
        QiskitError: when invalid command is provided
    """

    qobj_converter = SuperConverter(PulseQobjInstruction, **dict_config)

    if isinstance(schedules, ConditionedSchedule):
        schedules = [schedules]

    experiments = []

    default_qubit_lo_freq = dict_config.get('qubit_lo_freq', None)
    default_meas_lo_freq = dict_config.get('meas_lo_freq', None)

    user_pulselib = set()
    for exp_idx, conditioned in enumerate(schedules):
        # use LO frequency configs
        lo_freqs = {}
        if conditioned.user_lo_dict:
            if default_qubit_lo_freq:
                user_qubit_los = _replaced_with_user_los(conditioned.user_lo_dict,
                                                         default_qubit_lo_freq)
                if user_qubit_los != default_qubit_lo_freq:
                    lo_freqs['qubit_lo_freq'] = user_qubit_los
            if default_meas_lo_freq:
                user_meas_los = _replaced_with_user_los(conditioned.user_lo_dict,
                                                        default_meas_lo_freq)
                if user_meas_los != default_meas_lo_freq:
                    lo_freqs['meas_lo_freq'] = user_meas_los

        # generate experimental configuration
        experimentconfig = PulseQobjExperimentConfig(**lo_freqs)

        # generate experimental header
        experimentheader = QobjExperimentHeader(name=conditioned.name or 'Experiment-%d' % exp_idx)

        commands = []
        for instruction in conditioned.schedule.flat_instruction_sequence():
            # TODO: support conditional gate
            commands.append(qobj_converter(instruction))

            if isinstance(instruction, DriveInstruction):
                # add samples to pulse library
                user_pulselib.add(instruction.command)

        experiments.append(PulseQobjExperiment(instructions=commands,
                                               header=experimentheader,
                                               config=experimentconfig))

    # generate qobj pulse library
    qobj_default_pulselib = [QobjPulseLibrary(name=p['name'], samples=p['samples'])
                             for p in dict_config.get('pulse_library', [])]
    qobj_user_pulselib = [QobjPulseLibrary(name=p.name, samples=p.samples)
                          for p in user_pulselib]

    dict_config['pulse_library'] = qobj_default_pulselib + qobj_user_pulselib

    qobj_config = PulseQobjConfig(**dict_config)
    qobj_header = QobjHeader(**dict_header)

    return PulseQobj(qobj_id=str(uuid.uuid4()), config=qobj_config,
                     experiments=experiments, header=qobj_header)
