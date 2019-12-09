# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class LinearCounter:
    """
    Linear counter.

    The linear counter functions the same way is the length counter,
    except the value loaded into it is the exact number of clocks
    before muting the channel.

    There is an extra control flag. When the control flag is reset
    then the halted flag will be reset on every clock.
    """

    __slots__ = "_counter", "_is_halted", "_control", "_reload_value"

    def __init__(self):
        """
        """
        self._counter = 0
        self._control = False
        self._reload_value = 0
        self._is_halted = False

    def write(self, value):
        """
        Update the control flag and reload value.
        """
        self._control = bool(value & 0b10000000)
        self._reload_value = value & 0b1111111

    def clock(self):
        """
        Clock the counter.
        """
        if self._is_halted:
            self._counter = self._reload_value
        elif self._counter > 0:
            self._counter -= 1

        if self._control is False:
            self._is_halted = False

    @property
    def halted(self):
        """
        ``True``if the counter is halted, ``False`` if not.
        """
        return self._is_halted

    @halted.setter
    def halted(self, is_halted):
        """
        Set the halted flag.
        """
        self._is_halted = is_halted

    @property
    def active(self):
        """
        ``True`` is the counter is non-zero, ``False`` otherwise.
        """
        return self._counter > 0
