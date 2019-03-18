# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""
Schedule.
"""
import logging
from abc import ABCMeta, abstractmethod
from typing import List, Union

from qiskit.pulse.channels import PulseChannel, ChannelBank
from qiskit.pulse.commands import PulseCommand, FunctionalPulse, SamplePulse
from qiskit.pulse.exceptions import ScheduleError

logger = logging.getLogger(__name__)


class TimedPulseBlock(metaclass=ABCMeta):
    """
    Common interface of TimedPulse and PulseSchedule (Component in the Composite Pattern)."""

    @abstractmethod
    def start_time(self) -> int:
        pass

    @abstractmethod
    def end_time(self) -> int:
        pass

    @abstractmethod
    def duration(self) -> int:
        pass

    @abstractmethod
    def children(self) -> List['TimedPulseBlock']:
        pass


class TimedPulse(TimedPulseBlock):
    """TimedPulse = Pulse with start time context."""

    def __init__(self, pulse_command: PulseCommand, to_channel: PulseChannel, start_time: int):
        if isinstance(pulse_command, to_channel.__class__.supported):
            self.command = pulse_command
            self.channel = to_channel
            self.t0 = start_time
        else:
            raise ScheduleError("%s (%s) is not supported on %s (%s)" % (
                                pulse_command.__class__.__name__, pulse_command.name,
                                to_channel.__class__.__name__, to_channel.name))

    def start_time(self) -> int:
        return self.t0

    def end_time(self) -> int:
        return self.t0 + self.command.duration

    def duration(self) -> int:
        return self.command.duration

    def children(self) -> List[TimedPulseBlock]:
        return None


class PulseSchedule(TimedPulseBlock):
    """Schedule."""

    def __init__(self,
                 channel_bank: ChannelBank,
                 name: str = None
                 ):
        """Create empty schedule.

        Args:
            channels:
            name:
        """
        self._name = name
        self._channel_bank = channel_bank
        self._children = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def channels(self) -> ChannelBank:
        return self._channel_bank

    def add(self,
            commands: Union[PulseCommand, List[PulseCommand]],
            channel: PulseChannel,
            start_time: int):
        """Add new pulse command(s) with channel and start time context.

        Args:
            commands (PulseCommand|list):
            channel:
            start_time:
        """
        if isinstance(commands, PulseCommand):
            try:
                self.add_block(TimedPulse(commands, channel, start_time))
            except ScheduleError as err:
                logger.warning("Fail to add %s to %s at %s", commands, channel, start_time)
                raise ScheduleError(err.message)
        elif isinstance(commands, list):
            for cmd in commands:
                self.add(cmd, channel, start_time)

    def add_block(self, block: TimedPulseBlock):
        """Add a new composite pulse `TimedPulseBlock`.

        Args:
            block:
        """
        if isinstance(block, PulseSchedule):
            if self._channel_bank != block._channel_bank:
                raise ScheduleError("Additional block must have the same channels as self")

        if self._is_occupied_time(block):
            logger.warning("A pulse block is not added due to the occupied timing: %s", str(block))
            raise ScheduleError("Cannot add to occupied time slot.")
        else:
            self._children.append(block)

    def start_time(self) -> int:
        return min([self._start_time(child) for child in self._children])

    def end_time(self) -> int:
        return max([self._end_time(child) for child in self._children])

    def duration(self) -> int:
        return self.end_time() - self.start_time()

    def children(self) -> List[TimedPulseBlock]:
        return self._children

    def _start_time(self, block: TimedPulseBlock) -> int:
        if isinstance(block, TimedPulse):
            return block.start_time()
        else:
            return min([self._start_time(child) for child in block.children()])

    def _end_time(self, block: TimedPulseBlock) -> int:
        if isinstance(block, TimedPulse):
            return block.end_time()
        else:
            return max([self._end_time(child) for child in block.children()])

    def _is_occupied_time(self, timed_pulse) -> bool:
        # TODO: This is still a MVP, very very naive implementation
        if not isinstance(timed_pulse, TimedPulse):
            raise NotImplementedError()
        for pulse in self.flat_pulse_sequence():
            if pulse.channel == timed_pulse.channel:
                # interval check
                if pulse.start_time() < timed_pulse.end_time() \
                        and timed_pulse.start_time() < pulse.end_time():
                    return True
        return False

    def get_sample_pulses(self) -> List[PulseCommand]:
        # TODO: This is still a MVP
        for child in self._children:
            if not isinstance(child, TimedPulse):
                raise NotImplementedError()
        # TODO: Naive implementation (compute at add and remove would be better)
        lib = []
        for tp in self._children:
            if isinstance(tp.command, (FunctionalPulse, SamplePulse)) and \
                    tp.command not in lib:
                lib.append(tp.command)
        return lib

    def flat_pulse_sequence(self) -> List[TimedPulse]:
        # TODO: This is still a MVP
        for child in self._children:
            if not isinstance(child, TimedPulse):
                raise NotImplementedError()
        return self._children