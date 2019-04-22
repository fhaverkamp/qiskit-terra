# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""
ScheduleComponent, a common interface for components of schedule (Instruction and Schedule).
"""
from abc import ABCMeta, abstractmethod
from typing import Tuple, List

from qiskit.pulse.commands import Instruction

from .timeslots import TimeslotCollection


class ScheduleComponent(metaclass=ABCMeta):
    """Common interface for components of schedule. """

    @property
    @abstractmethod
    def duration(self) -> int:
        """Duration of this schedule component. """
        pass

    @property
    @abstractmethod
    def start_time(self) -> int:
        """Starting time of this schedule component. """
        pass

    @property
    @abstractmethod
    def stop_time(self) -> int:
        """Stopping time of this schedule component. """
        pass

    @abstractmethod
    def ch_duration(self, *channels) -> int:
        """Duration of the `channels` in schedule component. """
        pass

    @abstractmethod
    def ch_start_time(self) -> int:
        """Starting time of the `channels` in schedule component. """
        pass

    @abstractmethod
    def ch_stop_time(self) -> int:
        """Stopping of the `channels` in schedule component. """
        pass

    @property
    @abstractmethod
    def timeslots(self) -> TimeslotCollection:
        """Occupied time slots by this schedule component. """
        pass

    @property
    @abstractmethod
    def children(self) -> Tuple['ScheduleComponent', ...]:
        """Child nodes of this schedule component. """
        pass

    @abstractmethod
    def union(self, *schedules: List['ScheduleComponent']) -> 'ScheduleComponent':
        """Return a new schedule which is the union of the parent `Schedule` and `schedule`.

        Args:
            schedules: Schedules to be take the union with the parent `Schedule`.
        """
        pass

    @abstractmethod
    def shift(self: 'ScheduleComponent', time: int) -> 'ScheduleComponent':
        """Return a new schedule shifted forward by `time`.

        Args:
            time: Time to shift by
        """
        pass

    @abstractmethod
    def insert(self, start_time: int, schedule: 'ScheduleComponent') -> 'ScheduleComponent':
        """Return a new schedule with `schedule` inserted at `start_time` of `self`.

        Args:
            start_time: time to be inserted
            schedule: schedule to be inserted
        """
        pass

    @abstractmethod
    def append(self, schedule: 'ScheduleComponent') -> 'ScheduleComponent':
        """Return a new schedule with `schedule` inserted at the maximum time over
        all channels shared between `self` and `schedule`.

        Args:
            schedule: schedule to be appended
        """
        pass

    @abstractmethod
    def __add__(self, schedule: 'ScheduleComponent') -> 'ScheduleComponent':
        """Return a new schedule with `schedule` inserted within `self` at `start_time`."""
        pass

    @abstractmethod
    def __or__(self, schedule: 'ScheduleComponent') -> 'ScheduleComponent':
        """Return a new schedule which is the union of `self` and `schedule`."""
        pass

    @abstractmethod
    def __lshift__(self, time: int) -> 'ScheduleComponent':
        """Return a new schedule which is shifted forward by `time`."""
        return self.shift(time)

    @abstractmethod
    def __rshift__(self, time: int) -> 'ScheduleComponent':
        """Return a new schedule which is shifted backwards by `time`."""
        return self.shift(-time)
