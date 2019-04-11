# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""Helper class to assemble pulse instruction to PulseQobjInstruction."""

import functools
import inspect

from qiskit.pulse import commands
from qiskit.pulse.exceptions import PulseError
from qiskit.qobj import QobjMeasurementOption


def bind_instruction(type_instruction):
    """ Converter decorator method.

    Pulse instruction converter is defined for each instruction type,
    and this decorator binds converter function to valid instruction type.

    Args:
        type_instruction: valid pulse instruction class to the converter.
    """
    def _apply_converter(converter):
        """Return decorated converter function."""
        # pylint: disable=missing-return-doc

        @functools.wraps(converter)
        def _call_valid_converter(self, instruction):
            """Return dictionary for qobj if the given instruction matches to the
            bound instruction type to the function, otherwise just return None."""
            if isinstance(instruction, type_instruction):
                return converter(self, instruction)
            else:
                return None
        return _call_valid_converter
    return _apply_converter


class PulseQobjConverter:
    """
    This class exists for separating entity of pulse instructions and qobj instruction,
    and provides some alleviation of the complexity of the assembler.

    Converter is constructed with qobj model and some experimental configuration,
    and returns proper qobj instruction to each backend.

    Pulse instruction and its qobj are strongly depends on the design of backend,
    and third party providers can be easily add their custom pulse instruction by
    providing custom converter inherit from this.


    To create custom converter for custom instruction
    ```
    class CustomConverter(PulseQobjConverter):

        @bind_instruction(CustomInstruction)
        def _convert_custom_command(self, instruction):
            command_dict = {
                'name': 'custom_command',
                't0': instruction.start_time,
                'param1': instruction.param1,
                'param2': instruction.param2
            }
            if self._exp_config('option1', True):
                command_dict.update({
                    'param3': instruction.param3
                })
            return self.qobj_model(**command_dict)
    ```

    The name of converter method should start with `_convert_` otherwise it is ignored.
    Provided fields are automatically serialized by given qobj model.
    """

    def __init__(self, qobj_model, **exp_config):
        """Create new converter.

        Args:
             qobj_model (QobjInstruction): marshmallow model to serialize to object.
        """
        self._qobj_model = qobj_model
        self._exp_config = exp_config

    def __call__(self, instruction):

        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name.startswith('_convert_'):
                dict_qobj = method(instruction)
                if dict_qobj:
                    return dict_qobj
        else:
            PulseError('Proper qobj for %s is not found.' % instruction.command)

    @bind_instruction(commands.AcquireInstruction)
    def _convert_acquire(self, instruction):
        """Return Acquire dict for Qobj.

        Args:
            instruction (AcquireInstruction): acquire instruction.
        Returns:
            dict: Dictionary of required parameters.
        """
        meas_level = self._exp_config.get('meas_level', 2)

        command_dict = {
            'name': 'acquire',
            't0': instruction.start_time,
            'duration': instruction.duration,
            'qubits': [q.index for q in instruction.qubits],
            'memory_slot': [m.index for m in instruction.mem_slots]
        }
        if meas_level == 2:
            # setup discriminators
            if instruction.command.discriminator:
                command_dict.update({
                    'discriminators': [
                        QobjMeasurementOption(
                            name=instruction.command.discriminator.name,
                            params=instruction.command.discriminator.params)
                    ]
                })
            else:
                command_dict.update({
                    'discriminators': []
                })
            # setup register_slots
            command_dict.update({
                'register_slot': [regs.index for regs in instruction.reg_slots]
            })
        if meas_level >= 1:
            # setup kernels
            if instruction.command.kernel:
                command_dict.update({
                    'kernels': [
                        QobjMeasurementOption(
                            name=instruction.command.kernel.name,
                            params=instruction.command.kernel.params)
                    ]
                })
            else:
                command_dict.update({
                    'kernels': []
                })
        return self._qobj_model(**command_dict)

    @bind_instruction(commands.FrameChangeInstruction)
    def _convert_frame_change(self, instruction):
        """Return FrameChange dict for Qobj.

        Args:
            instruction (FrameChangeInstruction): frame change instruction.
        Returns:
            dict: Dictionary of required parameters.
        """
        command_dict = {
            'name': 'fc',
            't0': instruction.start_time,
            'ch': instruction.channel.name,
            'phase': instruction.command.phase
        }
        return self._qobj_model(**command_dict)

    @bind_instruction(commands.PersistentValueInstruction)
    def _convert_persistent_value(self, instruction):
        """Return PersistentValue dict for Qobj.

        Args:
            instruction (PersistentValueInstruction): persistent value instruction.
        Returns:
            dict: Dictionary of required parameters.
        """
        command_dict = {
            'name': 'pv',
            't0': instruction.start_time,
            'ch': instruction.channel.name,
            'val': instruction.command.value
        }
        return self._qobj_model(**command_dict)

    @bind_instruction(commands.DriveInstruction)
    def _convert_drive(self, instruction):
        """Return Drive dict for Qobj.

        Args:
            instruction (DriveInstruction): drive instruction.
        Returns:
            dict: Dictionary of required parameters.
        """
        command_dict = {
            'name': instruction.command.name,
            't0': instruction.start_time,
            'ch': instruction.channel.name
        }
        return self._qobj_model(**command_dict)

    @bind_instruction(commands.Snapshot)
    def _convert_snapshot(self, instruction):
        """Return SnapShot dict for Qobj.

        Args:
            instruction (Snapshot): snapshot instruction.
        Returns:
            dict: Dictionary of required parameters.
        """
        command_dict = {
            'name': 'snapshot',
            't0': instruction.start_time,
            'label': instruction.label,
            'type': instruction.type
        }
        return self._qobj_model(**command_dict)
