# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""
Command definition module. Relates circuit gates to pulse commands.
"""
import numpy as np

from .commands import SamplePulse
from .exceptions import ScheduleError
from .schedule import PulseSchedule


def _preprocess_pulse_library(self, pulse_library):
    """Take pulse library and convert to dictionary of `SamplePulse`s.

    Args:
        pulse_library (dict or list): Unprocessed pulse_library. May be either
            a (list | dict) of (SamplePulse | np.ndarray).

    Returns:
        dict: Pulse library consisting of `SamplePulse`s
    """
    processed_pulse_library = {}

    if isinstance(pulse_library, dict):
        for name, pulse in pulse_library.items():
            if isinstance(pulse, SamplePulse):
                pulse.name = name
            else:
                pulse = SamplePulse(len(pulse), pulse, name)

            processed_pulse_library[name] = pulse
    else:
        for pulse in pulse_library:
            if not isinstance(pulse, SamplePulse):
                pulse = SamplePulse(len(pulse), pulse, name)

            name = pulse.name

            processed_pulse_library[name] = pulse

    return processed_pulse_library


def cmd_def_from_defaults(flat_cmd_def, pulse_library):
    """Create command definition from backend defaults output.
    Args:
        flat_cmd_def (list): Command definition list returned by backend
        pulse_library (list): dict or list of pulse library entries
    Returns:
        CmdDef
    """
    _pulse_library = self._preprocess_pulse_library(pulse_library)


class CmdDef:
    """Command definition class.
    Relates `Gate`s to `PulseSchedule`s.
    """

    def __init__(self):
        """Create command definition from backend.
        """
        self._cmd_dict = {}

    def add(self, cmd_name, qubits, schedule):
        """Add a command to the `CommandDefinition`

        Args:
            cmd_name (str): Name of the command
            qubits (list or tuple): Ordered list of qubits command applies to
            schedule (ParameterizedSchedule or Schedule): Schedule to be added
        """
        qubits = tuple(qubits)
        cmd_dict = self._cmd_dict.setdefault('cmd', {})
        cmd_dict[qubits] = schedule

    def has_cmd(self, cmd_name, qubits):
        """Has command of name with qubits.

        Args:
            cmd_name (str): Name of the command
            qubits (list or tuple): Ordered list of qubits command applies to

        Returns:
            bool
        """
        if cmd_name in self._cmd_dict:
            if qubits in self._cmd_dict[cmd_name]:
                return True
        return False

    def get(self, cmd_name, qubits, default=None):
        """Get command from command definition.
        Args:
            cmd_name (str): Name of the command
            qubits (list or tuple): Ordered list of qubits command applies to
            default (None or ParameterizedPulseSchedule or PulseSchedule): Default PulseSchedule
                to return if command is not in CmdDef.
        Returns:
            PulseSchedule or ParameterizedPulseSchedule

        Raises:
            ScheduleError
        """
        if self.has_cmd(cmd_name, qubits):
            return self._cmd_dict[cmd_name][qubits]
        elif default:
                return default
        else:
            raise ScheduleError('Command {name} for qubits {qubits} is not present'
                                'in CmdDef'.format(cmd_name, qubits))

    def pop(self, cmd_name, qubits, default=None):
        """Pop command from command definition.

        Args:
            cmd_name (str): Name of the command
            qubits (list or tuple): Ordered list of qubits command applies to
            default (None or ParameterizedPulseSchedule or PulseSchedule): Default PulseSchedule
                to return if command is not in CmdDef.
        Returns:
            PulseSchedule or ParameterizedPulseSchedule

        Raises:
            ScheduleError
        """
        if self.has_cmd(cmd_name, qubits):
            cmd_dict = self._cmd_dict[cmd_name]
            cmd = cmd_dict.pop(qubits)
            if not cmd_dict:
                self._cmd_dict.pop(cmd_name)
            return cmd
        elif default:
            return default
        else:
            raise ScheduleError('Command {name} for qubits {qubits} is not present'
                                'in CmdDef'.format(cmd_name, qubits))

    def cmd_types(self):
        """Return all command names available in CmdDef.

        Returns:
            list
        """

        return list(self._cmd_dict.keys())

    def cmds(self):
        """Returns list of all commands.

        Returns:
            (str, tuple, PulseSchedule or ParameterizedPulseSchedule): A tuple containing
                the command name, tuple of qubits the command applies to and the command
                schedule.
        """
        return list(self)

    def __iter__(self):
        """
        Returns:
            (str, tuple, PulseSchedule or ParameterizedPulseSchedule): A tuple containing
                the command name, tuple of qubits the command applies to and the command
                schedule.
        """
        for cmd_name, cmds in self._cmd_dict.items():
            for qubits, schedule in cmds.items():
                yield ((cmd_name, qubits), schedule)

    def __setitem__(self, key, item):
        """
        Args:
            key (str, *qubits): Command name followed by qubits command applies to in order.
        """
        self.add(key[0], key[1:], item)

    def __getitem__(self, key):
        """
        Args:
            key (str, *qubits): Command name followed by qubits command applies to in order.
        """
        return self.get(key[0], key[1:])
