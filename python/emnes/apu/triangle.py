# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.waveform_channel import WaveformChannel
from emnes.apu.linear_counter import LinearCounter
from emnes.apu.triangle_wave import TriangleWave


class Triangle(metaclass=WaveformChannel.metaclass):
    """
    Triangle channel.

    The channel contains a length counter and linear counter used to silence the
    channel and a triangle wave that outputs a signal. The channel can be
    enabled or disabled.
    """

    __slots__ = ("_linear_counter",)

    def __init__(self):
        self._linear_counter = LinearCounter()
        self._init_waveform(lambda: TriangleWave(self._length_counter, self._linear_counter))

    def write_byte(self, addr, value):
        """
        Route a write to the right triangle channel register.

        :param addr: Address of the register to write to.
        :param value: Value to write to the register.
        """
        if addr == 0x4008:
            self._length_counter.halted = bool(value & 0b10000000)
            self._linear_counter.write(value)
        elif addr == 0x4009:
            pass
        elif addr == 0x400A:
            self._waveform.update_period(low=value)
        elif addr == 0x400B:
            if self._is_enabled:
                # Writing to this register resets the length counter...
                self._length_counter.reload(value >> 3)
            self._linear_counter.halted = True

            # ... updates the period high ...
            self._waveform.update_period(high=(value & 0b111))
        else:
            raise RuntimeError(f"Wrong address {hex(addr)} for pulse channel.")

    @property
    def output(self):
        """
        Output value of the triangle channel.
        """
        return self._waveform.output

    def clock_length_counter(self):
        """
        Clocks the length counter.
        """
        self._length_counter.clock()

    def clock_linear_counter(self):
        """
        Clocks the linear counter.
        """
        self._linear_counter.clock()
