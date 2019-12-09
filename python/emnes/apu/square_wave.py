# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class SquareWave:

    DUTY_WAVEFORM = [
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0, 0, 0],
        [1, 1, 0, 0, 1, 1, 1, 1],
    ]

    __slots__ = (
        "_waveform_period_low",
        "_waveform_period_high",
        "_duty_cycle_index",
        "_duty_step",
        "_waveform_counter",
    )

    def __init__(self):
        self._waveform_period_low = 0
        self._waveform_period_high = 0
        self._waveform_counter = 0

        self._duty_cycle_index = 0
        self._duty_step = 0

    @property
    def waveform_period(self):
        # The period is always combined from the two values.
        # If one wanted to implement a vibrato, they would modify
        # the timer low bits only so that the period can oscillate
        # without resetting the _waveform_counter, since that
        # would restart the cycle counting until the next duty
        # step.
        return self._waveform_period_low | self._waveform_period_high

    @property
    def duty_cycle_index(self):
        return self._duty_cycle_index

    @duty_cycle_index.setter
    def duty_cycle_index(self, index):
        self._duty_cycle_index = index

    @property
    def output(self):
        return self.DUTY_WAVEFORM[self._duty_cycle_index][self._duty_step]

    def update_period(self, low=None, high=None, duty=None):
        if low is not None:
            self._waveform_period_low = low

        if high is not None:
            self._waveform_period_high = high

        if duty is not None:
            self._duty_step = duty

    def emulate(self):
        self._waveform_counter -= 1
        if self._waveform_counter < 0:
            # This counter is clocked at every second CPU cycle, but the
            # emulate method is called on every cycle, so we'll double
            # the counter.
            self._waveform_counter = (self.waveform_period + 1) * 2
            self._duty_step = (self._duty_step - 1) % 8
