# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.shift_register import ShiftRegister


class OutputUnit:

    __slots__ = ("_shift_register", "_output_level", "_is_silenced")

    def __init__(self):
        self._output_level = 0
        self._shift_register = ShiftRegister()
        self._is_silenced = True

    def start_cycle(self, sample_buffer):
        self._shift_register.load_sample(sample_buffer)
        self._is_silenced = sample_buffer is None

    def clock(self):
        if self._is_silenced is False:
            bit = self._shift_register.bit_0
            if self._output_level > 1 and bit == 0:
                self._output_level -= 2
            elif self._output_level < 126 and bit == 1:
                self._output_level += 2
        return self._shift_register.clock()

    @property
    def output_level(self):
        return self._output_level

    @output_level.setter
    def output_level(self, output_level):
        self._output_level = output_level
