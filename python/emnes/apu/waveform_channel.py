# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.length_counter import LengthCounter


class WaveformChannel:
    """
    Common methods for the waveform channel.

    Do not inherit from this class. Instead, use the
    metaclass in order to directly inject the methods
    on the class. It seems like this makes the code run
    faster in PyPy.
    """

    class metaclass(type):
        def __new__(cls, name, bases, dctn):
            """
            Inject all methods from WaveformChannel into the
            ``dict`` of the new class.
            """
            dctn["__slots__"] += WaveformChannel.__slots__
            dctn["_init_waveform"] = WaveformChannel._init_waveform
            dctn["length_counter"] = WaveformChannel.length_counter
            dctn["emulate"] = WaveformChannel.emulate
            dctn["enabled"] = WaveformChannel.enabled
            dctn["active"] = WaveformChannel.active

            return type.__new__(cls, name, bases, dctn)

    __slots__ = ("_waveform", "_is_enabled", "_length_counter")

    def _init_waveform(self, waveform_factory):
        """
        param callable waveform_factory: Factory for the waveform.
        """
        self._length_counter = LengthCounter()
        self._is_enabled = False
        self._waveform = waveform_factory()

    @property
    def length_counter(self):
        """
        Access the length counter.
        """
        return self._length_counter

    def emulate(self):
        """
        Emulate the pulse channel.
        """
        self._waveform.emulate()

    @property
    def enabled(self):
        """
        ``True`` if the channel is enabled, ``False`` otherwise.
        """
        return self._is_enabled

    @enabled.setter
    def enabled(self, is_enabled):
        """
        Enable/disable the channel.

        When disable, playback is stopped by setting the length counter to 0.
        """
        self._is_enabled = is_enabled
        if is_enabled is False:
            self._length_counter.reload(None)

    @property
    def active(self):
        """
        ``True`` if the channel is still playing, ``False`` otherwise.
        """
        return self._length_counter.active
