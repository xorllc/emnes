# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.frame_sequencer import FrameSequencer


class Status:
    """
    Status register.

    This register can be used to enable/disable a channel or to
    know if a channel still has samples to play back before
    silencing itself.
    """

    __slots__ = "_pulse_4000", "_pulse_4004", "_triangle", "_dmc", "_noise"

    def __init__(self, pulse_4000, pulse_4004, triangle, noise, dmc):
        """
        :param emnes.apu.pulse.Pulse pulse_4000: Pulse channel starting a 0x4000
        :param emnes.apu.pulse.Pulse pulse_4004: Pulse channel starting a 0x4004
        :param emnes.apu.triangle.Triangle triangle: Triangle channel
        :param emnes.apu.noise.Noise noise: Noise channel
        :param emnes.apu.dmc.DMC dmc: DMC channel
        """
        self._pulse_4000 = pulse_4000
        self._pulse_4004 = pulse_4004
        self._triangle = triangle
        self._noise = noise
        self._dmc = dmc

    def write_byte(self, value):
        """
        Enable/disable the audio channels.

        :param value: Value used to enable/disable the channels.
        """
        self._pulse_4000.enabled = bool(value & 1)
        self._pulse_4004.enabled = bool(value & 2)
        self._triangle.enabled = bool(value & 4)
        self._noise.enabled = bool(value & 8)
        self._dmc.enabled = bool(value & 16)

    def read_byte(self):
        """
        Get the active state of each channel.

        :returns: The active state of each channel.
        """
        return (
            int(self._pulse_4000.active)
            | (int(self._pulse_4004.active) << 1)
            | (int(self._triangle.active) << 2)
            | (int(self._noise.active) << 3)
            | (int(self._dmc.active) << 4)
        )
