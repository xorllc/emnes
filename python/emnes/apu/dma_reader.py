# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class DMAReader:
    """
    DMA Reader.

    Reads bytes from memory until all bytes have been read, or restarts
    if the looping flag is set.
    """

    __slots__ = (
        "_current_address",
        "_bytes_remaining",
        "_memory_bus",
        "_start_address",
        "_length",
        "_is_looping",
    )

    def __init__(self, memory_bus):
        """
        :param memory_bus: MemoryBus used to read the samples from memory.
        """
        self._memory_bus = memory_bus
        self._current_address = 0
        self._bytes_remaining = 0
        self._start_address = 0
        self._length = 0
        self._is_looping = False

    def restart(self):
        """
        Restarts a an audio clip from the beginning.
        """
        self._current_address = self._start_address
        self._bytes_remaining = self._length

    def clear(self):
        """
        Stop reading samples immediately.
        """
        self._bytes_remaining = 0

    @property
    def active(self):
        """
        ``True`` if more samples can be read from memory.
        """
        return self._bytes_remaining != 0

    @property
    def bytes_remaining(self):
        """
        Number of bytes left to read.
        """
        return self._bytes_remaining

    def read_byte(self):
        """
        Read the next byte from memory.
        """
        # Read a byte
        value = self._memory_bus.read_byte(self._current_address)

        # Move to the next one and handle wrap-around.
        self._current_address += 1
        if self._current_address > 0xFFFF:
            self._current_address = 0x8000

        # One less byte to read.
        self._bytes_remaining -= 1
        # IF we're empty and looping, restart.
        if self._bytes_remaining == 0 and self._is_looping:
            self.restart()

        return value

    @property
    def is_looping(self):
        """
        ``True`` is looping audio clip, ``False`` otherwise.
        """
        return self._is_looping

    @is_looping.setter
    def is_looping(self, is_looping):
        """
        Set the looping flag.
        """
        self._is_looping = is_looping

    @property
    def start_address(self):
        """
        Address of the first byte of the audio clip to play.
        """
        return self._start_address

    @start_address.setter
    def start_address(self, start_address):
        """
        Set the of the first byte of the audio clip to play.
        """
        self._start_address = start_address

    @property
    def length(self):
        """
        Length of the audio clip to play.
        """
        return self._length

    @length.setter
    def length(self, length):
        """
        Set the length of the audio clip to play.
        """
        self._length = length
