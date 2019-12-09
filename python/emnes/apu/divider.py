# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class Divider:
    """
    Implements a down counter that gets reloaded with a specified period
    everytime it reaches zero.
    """

    __slots__ = ("_counter", "_period")

    def __init__(self, counter=1, period=1):
        """
        :param int counter: Initial value of the counter. Defaults to 0.
        :param int period: Initial value of the period. Defaults to 1.
        """
        assert counter > 0
        self._counter = counter
        self._period = period

    def clock(self):
        """
        Clock the divider.

        If the count reaches 0, it is reloaded with the period.

        :returns: ``True`` if the counter was reloaded, ``False`` otherwise.
        """
        self._counter -= 1
        if self._counter == 0:
            self._counter = self._period
            return True
        else:
            return False

    @property
    def counter(self):
        """
        Current counter value.
        """
        return self._counter

    @property
    def period(self):
        """
        Period of the divider.
        """
        return self._period

    @period.setter
    def period(self, period):
        """
        Update the period of the divider.
        """
        self._period = period

    def reload(self):
        """
        Reload the counter with the period.
        """
        self._counter = self._period
