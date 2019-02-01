# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

# pylint: disable=invalid-name,missing-docstring,missing-param-doc

"""
Acquire
"""

from qiskit.pulse.commands.pulse_command import PulseCommand


class Acquire(PulseCommand):
    """Acquire."""

    def __init__(self, qubit, memoly_slot,
                 register_slot=None, discriminator=None, kernel=None):
        """create new acquire command

        Parameters:
            qubit (int):  index of the qubits to measure during this acquisition.

            memoly_slot (int): index of the classical memory slots to store the measurement
            results. the total number of memory slots is specified through the Qobj memory slot
            numbering starts at 0, and memory slots can be overwritten if they are specified
            twice in the same experiment (separate experiments have separate memories)

            register_slot (int): index of the classical register slots to store the
            measurement results. the total number of register slots is specified specified by
            the backend. this is only allowed if the backend supports conditionals and the
            memory level is 2 (discriminated). registers can only accept bits.

            discriminator (Discriminator): discriminators to be used (from the list of available
            discrimi-nator) if the measurement level is 2.

            kernel (Kernel): the data structures defining the measurement kernels to be used
            (from the list of available kernels) and set of parameters (if applicable)
            if the measurement level is 1 or 2.
        """

        super(Acquire, self).__init__(0)

        self.qubit = qubit
        self.memory_slot = memoly_slot
        self.register_slot = register_slot

        if discriminator:
            self.discriminator = discriminator
        else:
            self.discriminator = Discriminator()

        if kernel:
            self.kernel = kernel
        else:
            self.kernel = Kernel()


class Discriminator:
    """Discriminator"""

    def __init__(self, name="max_1Q_fidelity", params=[0, 0]):
        """create new discriminator

        Parameters:
            name (str): name of discriminator to be used
            params (list): list of parameters
        """
        self.name = name
        self.params = params


class Kernel:
    """Kernel"""

    def __init__(self, name="boxcar", params=[]):
        """create new kernel

        Parameters:
            name (str): name of kernel to be used
            params (list): list of parameters
        """
        self.name = name
        self.params = params
