# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.divider import Divider


class Envelope:
    """
    Envelope.

    Controls the volume of the channel. It can either play a sound at a constant
    volume or play a sound that becomes softer ofter time.
    """

    __slots__ = (
        "_counter",
        "_constant_volume",
        "_is_constant",
        "_is_looping",
        "_divider",
        "_write_since_last_clock",
    )

    def __init__(self):
        """
        """
        self._counter = 15
        self._constant_volume = 15
        self._is_constant = True
        self._is_looping = False
        self._divider = Divider()
        self._write_since_last_clock = False

    def write(self, value):
        """
        Update the envelope.

        :param value: Value updating the envelope various parameters.
        """
        period_or_volume = value & 0xF
        self._divider.period = period_or_volume + 1
        self._constant_volume = period_or_volume
        self._is_constant = bool(value & 0b10000)
        self._is_looping = bool(value & 0b100000)

    @property
    def write_since_last_clock(self):
        """
        ``True`` if a write has occurred since the envelope was clocked, ``False``
        otherwise.
        """
        return self._write_since_last_clock

    @write_since_last_clock.setter
    def write_since_last_clock(self, was_written):
        """
        Call when the period of the waveform was updated.
        """
        self._write_since_last_clock = was_written

    def clock(self):
        """
        Clock the envelope.

        This will reload the maximum volume value or soften the volume of the
        channel.
        """
        # If someone changed the period, we have to reload the divider
        # and the output volume
        if self._write_since_last_clock:
            self._write_since_last_clock = False
            self._counter = 15
            self._divider.reload()
        # Otherwise decrement the divider.
        elif self._divider.clock():
            # If the divider generated a clock, update the volume.
            # If we've reached the end of the volume counter,
            # reload it if looping, otherwise decrement the volume
            # if not silenced.
            if self._is_looping and self._counter == 0:
                self._counter = 15
            elif self._counter != 0:
                self._counter -= 1

        assert self._counter >= 0

    @property
    def volume(self):
        """
        Current volume for the channel.
        """
        if self._is_constant:
            return self._constant_volume
        else:
            return self._counter
