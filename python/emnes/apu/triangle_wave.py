# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.length_counter import LengthCounter
from emnes.apu.linear_counter import LinearCounter


class TriangleWave:

    __slots__ = (
        "_waveform_period_low",
        "_waveform_period_high",
        "_waveform_counter",
        "_length_counter",
        "_linear_counter",
        "_duty_step",
    )

    # 15 to 0 and then 0 to 15
    TRIANGLE_WAVEFORM = list(range(15, -1, -1)) + list(range(0, 16))

    def __init__(self, length_counter, linear_counter):
        self._waveform_period_low = 0
        self._waveform_period_high = 0
        self._waveform_counter = 0
        self._length_counter = length_counter
        self._linear_counter = linear_counter
        self._duty_step = 0

    def update_period(self, low=None, high=None):
        if low is not None:
            self._waveform_period_low = low

        if high is not None:
            self._waveform_period_high = high

    def emulate(self):
        self._waveform_counter -= 1
        if self._waveform_counter < 0:
            self._waveform_counter = self._waveform_period
            if self._length_counter.active and self._linear_counter.active:
                self._duty_step = (self._duty_step + 1) % 32

    @property
    def output(self):
        if self._waveform_period_low < 2 and self._waveform_period_high == 0:
            return 7
        else:
            return self.TRIANGLE_WAVEFORM[self._duty_step]

    @property
    def _waveform_period(self):
        # The period is always combined from the two values.
        # If one wanted to implement a vibrato, they would modify
        # the timer low bits only so that the period can oscillate
        # without resetting the _waveform_counter, since that
        # would restart the cycle counting until the next duty
        # step.
        return (self._waveform_period_low | (self._waveform_period_high << 8)) + 1
