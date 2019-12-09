# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.divider import Divider


class NoiseShiftRegister:
    """
    Noise shift Register

    It generates a noise sample by shifting bits around.
    """

    __slots__ = ("_is_short_mode", "_divider", "_shift")

    # fmt: off
    PERIOD_LOOKUP = [
        0x004,
        0x008,
        0x010,
        0x020,
        0x040,
        0x060,
        0x080,
        0x0A0,
        0x0CA,
        0x0FE,
        0x17C,
        0x1FC,
        0x2FA,
        0x3F8,
        0x7F2,
        0xFE4,
    ]
    # fmt: on

    def __init__(self, shift=1, is_short_mode=False):
        """
        :param shift: Initial value in the shifter. Defaults to 1.
        :param is_short_mode: Select the mode for the noise.
        """
        self._is_short_mode = is_short_mode
        self._divider = Divider(period=self.PERIOD_LOOKUP[0])
        self._shift = shift

    def write(self, value):
        """
        Update the noise's period and mode.

        :param value: Value that will update the register.
        """
        self._divider.period = self.PERIOD_LOOKUP[value & 0xF]
        self._is_short_mode = bool(0x80 & value)

    def emulate(self):
        """
        Emulate the shift register behavior.
        """
        # When the divider clocks, shift the bits.
        if self._divider.clock():
            # In short mode, we XOR bit 0 and 6. In long mode,
            # 0 and 1 are XORed. We then shift the
            # register and put the result of the shift at bit 14.
            new_bit_14 = (self._shift & 1) ^ (
                (self._shift >> (6 if self._is_short_mode else 1)) & 1
            )
            self._shift >>= 1
            self._shift |= new_bit_14 << 14

    @property
    def shift(self):
        """
        Current value of the shift.
        """
        return self._shift

    @property
    def counter(self):
        """
        Current value of the counter.
        """
        return self._divider.counter

    @property
    def is_short_mode(self):
        """
        ``True`` if the shift register is in short mode, ``False`` otherwise.
        """
        return self._is_short_mode

    @property
    def period(self):
        """
        Period of the divider.
        """
        return self._divider.period

    @property
    def output(self):
        """
        Output sample of the shift register. If the lsb is 0, outputs
        1 otherwise outputs 0.
        """
        return (~self._shift) & 1
