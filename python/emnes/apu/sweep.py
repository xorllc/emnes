# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


from emnes.apu.divider import Divider


class Sweep:

    __slots__ = (
        "_is_sweeping",
        "_is_negating",
        "_shift",
        "_write_since_last_clock",
        "_divider",
        "_square_wave",
        "_length_counter",
        "_is_pulse_1",
    )

    def __init__(self, square_wave, length_counter, is_pulse_1):
        self._is_sweeping = False
        self._divider = Divider()
        self._is_negating = False
        self._shift = 0

        self._write_since_last_clock = False

        self._square_wave = square_wave
        self._length_counter = length_counter
        self._is_pulse_1 = is_pulse_1

    def write(self, value):
        self._is_sweeping = bool(value & 0b10000000)
        self._is_negating = bool(value & 0b1000)
        self._divider.period = ((value >> 4) & 0b111) + 1
        self._shift = value & 0b111
        self._write_since_last_clock = True

    def _compute_new_period(self):
        offset = self._square_wave.waveform_period >> self._shift
        if self._is_negating:
            if self._is_pulse_1:
                offset = -offset - 1
            else:
                offset = -offset
        return self._square_wave.waveform_period + offset

    def clock(self):
        was_reset = self._divider.clock()

        if self._write_since_last_clock or was_reset:
            self._write_since_last_clock = False

        if was_reset and self.is_muting is False and self._is_sweeping:
            new_period = self._compute_new_period()
            self._square_wave.update_period(new_period & 0xFF, new_period & 0x0700)

    @property
    def is_muting(self):
        if self._square_wave.waveform_period < 8:
            return True
        if self._compute_new_period() > 0x7FF:
            return True
        return False
