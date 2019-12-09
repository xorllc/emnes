# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


from emnes.apu.envelope import Envelope
from emnes.apu.waveform_channel import WaveformChannel
from emnes.apu.noise_shift_register import NoiseShiftRegister


class Noise(metaclass=WaveformChannel.metaclass):
    """
    Noise channel.
    """

    __slots__ = ("_envelope",)

    def __init__(self):
        """
        """
        self._init_waveform(NoiseShiftRegister)
        self._envelope = Envelope()

    def write_byte(self, addr, value):
        """
        Route a write to the right triangle channel register.

        :param addr: Address of the register to write to.
        :param value: Value to write to the register.
        """
        if addr == 0x400C:
            self._envelope.write(value & 0b111111)
            self._length_counter.halted = bool(value & 0b100000)
        elif addr == 0x400D:
            pass
        elif addr == 0x400E:
            self._waveform.write(value)
        elif addr == 0x400F:
            if self._is_enabled:
                # Writing to this register resets the length counter...
                self._length_counter.reload(value >> 3)
            self._envelope.write_since_last_clock = True
        else:
            raise RuntimeError(f"Wrong address {hex(addr)} for pulse channel.")

    @property
    def output(self):
        """
        Current sample output from the channel.
        """
        if self._length_counter.active is False or self._is_enabled is False:
            return 0
        else:
            return self._waveform.output * self._envelope.volume

    def clock_length_counter(self):
        """
        Clock the length counter.
        """
        self._length_counter.clock()

    def clock_envelope_counter(self):
        """
        Clock the envelope counter.
        """
        self._envelope.clock()
