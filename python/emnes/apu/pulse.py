# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.waveform_channel import WaveformChannel
from emnes.apu.square_wave import SquareWave
from emnes.apu.sweep import Sweep
from emnes.apu.envelope import Envelope


class Pulse(metaclass=WaveformChannel.metaclass):
    """
    Pulse channel.

    The channel contains a length counter, a square wave generator,
    a sweep that changes the period of the wave and an envelope
    that allows to dynamically change the volume of a note
    over time.

    This class can be used with both pulse channels. Passing in the
    base address will allow to implement it's behavior properly.
    """

    __slots__ = ("_base_addr", "_sweep", "_envelope")

    def __init__(self, base_addr):
        """
        param int base_addr: Base address of the pulse channel. Can be
            0x4000 or 0x4004.
        """
        self._init_waveform(SquareWave)
        self._base_addr = base_addr
        self._sweep = Sweep(self._waveform, self._length_counter, base_addr == 0x4000)
        self._envelope = Envelope()

    @property
    def square_wave(self):
        """
        Access the square wave.
        """
        return self._waveform

    def write_byte(self, addr, value):
        """
        Route a write to the right triangle channel register.

        :param addr: Address of the register to write to.
        :param value: Value to write to the register.
        """
        register_index = addr - self._base_addr
        if register_index == 0:
            # If the length counter should be halted.
            self._length_counter.halted = bool(value & 0b100000)
            # Changing the duty cycle type does not invalidate the
            # current duty step we're at.
            self._waveform.duty_cycle_index = value >> 6
            self._envelope.write(value & 0b111111)
        elif register_index == 1:
            self._sweep.write(value)
        elif register_index == 2:
            self._waveform.update_period(low=value)
        elif register_index == 3:
            if self._is_enabled:
                # Writing to this register resets the length counter...
                self._length_counter.reload(value >> 3)
            # ... updates the period high ...
            self._waveform.update_period(high=(value & 0b111) << 8, duty=0)
            self._envelope.write_since_last_clock = True
        else:
            raise RuntimeError(f"Wrong address {hex(addr)} for pulse channel.")

    @property
    def output(self):
        """
        Current sample output from the channel.
        """
        if (
            self._sweep.is_muting
            or self._length_counter.active is False
            or self._is_enabled is False
        ):
            return 0
        else:
            return self._waveform.output * self._envelope.volume

    def clock_length_counter(self):
        """
        Clock the length counter and sweep.
        """
        self._length_counter.clock()
        self._sweep.clock()

    def clock_envelope_counter(self):
        """
        Clock the envelope counter.
        """
        self._envelope.clock()
