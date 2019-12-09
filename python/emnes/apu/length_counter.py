# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class LengthCounter:
    """
    Length counter.

    The length counter is reloaded with a value taken from the
    # LENGHT_COUNTER_LOOKUP table and starts counting down. When
    the counter reaches 0, the channel is muted. The counter can
    be halted at any time and it stops counting down.
    """

    __slots__ = "_counter", "_is_halted"

    # This is the length counter lookup table. When writing to the 5 msb
    # of 0x4004/0x4008, the 5 bit value is used to index into this table
    # to know the length of a note.
    # bits  bit 3
    # 7-4   0   1
    #     -------
    # 0   $0A $FE
    # 1   $14 $02
    # 2   $28 $04
    # 3   $50 $06
    # 4   $A0 $08
    # 5   $3C $0A
    # 6   $0E $0C
    # 7   $1A $0E
    # 8   $0C $10
    # 9   $18 $12
    # A   $30 $14
    # B   $60 $16
    # C   $C0 $18
    # D   $48 $1A
    # E   $10 $1C
    # F   $20 $1E

    # fmt: off
    LENGTH_COUNTER_LOOKUP = [
        0x0A, 0xFE,
        0x14, 0x02,
        0x28, 0x04,
        0x50, 0x06,
        0xA0, 0x08,
        0x3C, 0x0A,
        0x0E, 0x0C,
        0x1A, 0x0E,
        0x0C, 0x10,
        0x18, 0x12,
        0x30, 0x14,
        0x60, 0x16,
        0xC0, 0x18,
        0x48, 0x1A,
        0x10, 0x1C,
        0x20, 0x1E,
    ]
    # fmt: on

    def __init__(self):
        """
        """
        self._counter = 0
        self._is_halted = False

    def clock(self):
        """
        Decrements the counter if not halted or 0.
        """
        if self._is_halted is False and self._counter > 0:
            self._counter -= 1

    @property
    def value(self):
        """
        Current value of the counter.
        """
        return self._counter

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

    def reload(self, index):
        """
        Reload the counter.

        If None, the counter is set to 0 and the channel is silenced
        immediately.
        """
        if index is None:
            self._counter = 0
        else:
            self._counter = self.LENGTH_COUNTER_LOOKUP[index]

    @property
    def active(self):
        """
        ``True`` is the counter is non-zero, ``False`` otherwise.
        """
        return self._counter > 0
