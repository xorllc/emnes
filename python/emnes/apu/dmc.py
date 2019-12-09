# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


from emnes.apu.output_unit import OutputUnit
from emnes.apu.dma_reader import DMAReader
from emnes.apu.divider import Divider


class DMC:
    """
    DMC channel.

    The delta module channel can output 1 bit deltas. It contains a dma reader
    that fills a sample buffer, which is then consumed by an output unit.
    """

    __slots__ = ("_output_unit", "_dma_reader", "_divider", "_sample_buffer")

    RATE_LOOKUP = [428, 380, 340, 320, 286, 254, 226, 214, 190, 160, 142, 128, 106, 84, 72, 54]

    def __init__(self, memory_bus):
        """
        :param emnes.memory_bus.MemoryBus memory_bus: Memory bus used to access
            DMC samples.
        """
        self._output_unit = OutputUnit()
        self._dma_reader = DMAReader(memory_bus)
        self._divider = Divider(428, 428)
        self._sample_buffer = None

    @property
    def dma_reader(self):
        """
        Access the DMA reader.
        """
        return self._dma_reader

    def write_byte(self, addr, value):
        """
        Route a write to the right register.

        :param addr: Address of the register to write to.
        :param value: Value to write at the register.
        """
        if addr == 0x4010:
            # We don't support APU IRQ's for now.
            assert value & 0x80 == 0, "APU IRQ's not supported."
            self._dma_reader.is_looping = bool(value & 0x40)
            self._divider.period = self.RATE_LOOKUP[value & 0xF]
            self._divider.reload()
        elif addr == 0x4011:
            self._output_unit.output_level = value & 0x7F
        elif addr == 0x4012:
            self._dma_reader.start_address = 0xC000 + value * 64
        elif addr == 0x4013:
            self._dma_reader.length = value * 16 + 1
        else:
            raise RuntimeError(f"Wrong address {hex(addr)} for pulse channel.")

    @property
    def output(self):
        """
        Current value output from the channel.
        """
        return self._output_unit.output_level

    def emulate(self):
        """
        Emulate one cycle of the channel.
        """
        if self._divider.clock():
            # Clock the output unit.
            # If the shift register was emptied, start a new cycle
            # by emptying in the sample buffer into the output unit...
            if self._output_unit.clock():
                self._output_unit.start_cycle(self._sample_buffer)
                self._sample_buffer = None
                # ... and then refill it if the dma reader still has more
                # bytes to read.
                if self._dma_reader.active:
                    self._sample_buffer = self._dma_reader.read_byte()

    def _set_enabled(self, enable):
        """
        Enable/disable the DMA reader and hence the channel.
        """
        if enable:
            if not self._dma_reader.active:
                self._dma_reader.restart()
        else:
            self._dma_reader.clear()

    enabled = property(None, _set_enabled)

    @property
    def active(self):
        """
        ``True`` if the channel is still playing, ``False`` otherwise.
        """
        return self._dma_reader.active
