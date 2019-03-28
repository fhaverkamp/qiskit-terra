# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

# pylint: disable=invalid-name,unexpected-keyword-arg

"""Test cases for the pulse schedule."""

import numpy as np

from qiskit.pulse.channels import DeviceSpecification, Qubit
from qiskit.pulse.channels import DriveChannel, AcquireChannel, RegisterSlot, ControlChannel
from qiskit.pulse.commands import function, FrameChange, Acquire, PersistentValue, Snapshot
from qiskit.pulse.schedule import Schedule
from qiskit.test import QiskitTestCase


class TestSchedule(QiskitTestCase):
    """Schedule tests."""

    def test_can_create_valid_schedule(self):
        """Test valid schedule creation without error.
        """

        @function
        def gaussian(duration, amp, t0, sig):
            x = np.linspace(0, duration - 1, duration)
            return amp * np.exp(-(x - t0) ** 2 / sig ** 2)

        gp0 = gaussian(duration=20, name='pulse0', amp=0.7, t0=9.5, sig=3)
        gp1 = gaussian(duration=20, name='pulse1', amp=0.5, t0=9.5, sig=3)

        qubits = [
            Qubit(0, drive_channels=[DriveChannel(0, 1.2)], control_channels=[ControlChannel(0)]),
            Qubit(1, drive_channels=[DriveChannel(1, 3.4)], acquire_channels=[AcquireChannel(1)])
        ]
        registers = [RegisterSlot(i) for i in range(2)]
        device = DeviceSpecification(qubits, registers)

        fc_pi_2 = FrameChange(phase=1.57)
        acquire = Acquire(10)
        sched = Schedule(device)
        sched.insert(0, gp0(device.q[0].drive))
        sched.insert(0, PersistentValue(value=0.2+0.4j)(device.q[0].control))
        sched.insert(30, gp1(device.q[1].drive))
        sched.insert(60, FrameChange(phase=-1.57)(device.q[0].drive))
        sched.insert(60, gp0(device.q[0].control))
        sched.insert(80, Snapshot("label", "snap_type"))
        sched.insert(90, fc_pi_2(device.q[0].drive))
        sched.insert(90, acquire(device.q[1], device.mem[1], device.c[1]))
        # print(sched)

        self.assertTrue(True)
