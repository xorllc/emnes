# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.pulse import Pulse
from emnes.apu.frame_sequencer import FrameSequencer
from emnes.apu.status import Status
from emnes.apu.triangle import Triangle
from emnes.apu.dmc import DMC
from emnes.apu.noise import Noise
from emnes.apu.mixer import Mixer


class APU:
    """
    This is the NES audio processing unit.

    Each sound channel is emulated into a separate class. Every few CPU cycles
    the output of each channel is read and sent to the mixer to generate
    an audio sample. Than sample is then inserted into the samples buffer.

    The samples property on the class that holds the sound samples ready
    to sent to an audio playback device. It needs to be called regularly
    of the buffer will overflow. Simply calling the samples method will
    return the new samples and empty the internal buffer.

    Missing:
    - When the DMC channels reads memory, the CPU idles 4 cycles. This
        has not been implemented.
    """

    __slots__ = (
        "_pulse_4000",
        "_pulse_4004",
        "_frame_sequencer",
        "_status",
        "_triangle",
        "_noise",
        "_dmc",
        "_sample_distance",
        "_sample_counter",
        "_sample_index",
        "_samples",
        "_mixer",
    )

    def __init__(self, memory_bus):
        """
        :param memory_bus: MemoryBus used for accessing RAM in the DMC channel.
        """
        # All the audio channels.
        self._pulse_4000 = Pulse(0x4000)
        self._pulse_4004 = Pulse(0x4004)
        self._triangle = Triangle()
        self._dmc = DMC(memory_bus)
        self._noise = Noise()

        # Audio mixer.
        self._mixer = Mixer()

        # Frame sequencer used to clock various counters in the audio channels.
        self._frame_sequencer = FrameSequencer(
            self._clock_length_handler, self._clock_envelope_handler
        )

        # Status register, used to know if each channel is outputting a single
        # and to enable/disable them.
        self._status = Status(
            self._pulse_4000, self._pulse_4004, self._triangle, self._noise, self._dmc
        )

        # Buffer of samples to be sent to an audio device. Holds up to a second
        # of samples.
        self._samples = bytearray(44100)
        # We'll generate a sample every few CPU cycles.
        self._sample_distance = 1789773 / len(self._samples)
        # This will count how many cpu cycles since the last time a sample
        # was producer.
        self._sample_counter = 0
        # The index of the next sample in the _samples array.
        self._sample_index = 0

    def write_byte(self, addr, value):
        """
        Route a write to the appropriate audio register.

        :param addr: Address to write to.
        :param value: Value to write to the register.
        """
        if addr < 0x4004:
            self._pulse_4000.write_byte(addr, value)
        elif addr < 0x4008:
            self._pulse_4004.write_byte(addr, value)
        elif addr < 0x400C:
            self._triangle.write_byte(addr, value)
        elif addr < 0x4010:
            self._noise.write_byte(addr, value)
            pass
        elif addr < 0x4014:
            self._dmc.write_byte(addr, value)
        elif addr == 0x4015:
            self._status.write_byte(value)
        elif addr == 0x4017:
            self._frame_sequencer.write_byte(value)

    def read_byte(self, addr):
        """
        Route a read to the approriate audio register.

        :param addr: Address to read to.
        """
        # Only the status register can be read. All others
        # return 0.
        if addr == 0x4015:
            return self._status.read_byte()
        else:
            return 0

    def emulate(self, nb_cycles):
        """
        Emulate one cycle of the APU.
        """
        for i in range(nb_cycles):
            # Each audio component needs to be emulated.
            self._frame_sequencer.emulate()
            self._pulse_4000.emulate()
            self._pulse_4004.emulate()
            self._triangle.emulate()
            self._noise.emulate()
            self._dmc.emulate()

            # Check if we have a new audio sample to produce.
            self._sample_counter += 1
            if self._sample_counter >= self._sample_distance:
                self._sample_counter -= self._sample_distance
                # Mix the samples using the mixer and output a sample.
                self._samples[self._sample_index] = self._mixer.mix(
                    self._pulse_4000.output,
                    self._pulse_4004.output,
                    self._triangle.output,
                    self._noise.output,
                    self._dmc.output,
                )
                self._sample_index += 1

    @property
    def samples(self):
        """
        Get some samples to be sent to an audio playback device.

        When this method is called, all the new samples are returned.
        Calling it again will return an empty buffer.
        """
        current_sample = self._sample_index
        self._sample_index = 0
        return self._samples[0:current_sample]

    @property
    def mixer(self):
        """
        Access the audio mixer.
        """
        return self._mixer

    def _clock_length_handler(self):
        """
        Clocks the length counter of the pulse channels,
        triangle and noise.
        """
        self._pulse_4000.clock_length_counter()
        self._pulse_4004.clock_length_counter()
        self._triangle.clock_length_counter()
        self._noise.clock_length_counter()

    def _clock_envelope_handler(self):
        """
        Clocks the envelope of the pulse channels,
        triangle and noise.
        """
        self._pulse_4000.clock_envelope_counter()
        self._pulse_4004.clock_envelope_counter()
        self._triangle.clock_linear_counter()
        self._noise.clock_envelope_counter()
