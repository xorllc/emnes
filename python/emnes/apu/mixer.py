# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class Mixer:
    """
    Audio mixer.

    It uses look up tables to approximate the sounds that should be output.
    The formula is taken from the apu_ref.txt doc.

    It is possible to use the various toggle_<channel-name> methods to
    turn on or off an audio channel.
    """

    __slots__ = "_pulse_1_mask", "_pulse_2_mask", "_triangle_mask", "_noise_mask", "_dmc_mask"

    SQUARE_SUM_LOOKUP = [0] + [95.52 / (8128.0 / n + 100) for n in range(1, 31)]

    # n can be as big as 3 * 15 (triangle * 3) + dmc (127)
    TRIANGLE_NOISE_CMD_TABLE = [0] + [
        163.67 / (24329.0 / n + 100) for n in range(1, 3 * 15 + 127 + 1)
    ]

    def __init__(self):
        self._pulse_1_mask = 0xFF
        self._pulse_2_mask = 0xFF
        self._triangle_mask = 0xFF
        self._noise_mask = 0xFF
        self._dmc_mask = 0xFF

    def mix(self, pulse_1, pulse_2, triangle, noise, dmc):
        """
        Mix the 5 audio channel and produce an audio sample between 0 and 255.
        """
        return int(
            (
                self.SQUARE_SUM_LOOKUP[
                    (pulse_1 & self._pulse_1_mask) + (pulse_2 & self._pulse_2_mask)
                ]
                + self.TRIANGLE_NOISE_CMD_TABLE[
                    3 * (triangle & self._triangle_mask)
                    + 2 * (noise & self._noise_mask)
                    + (dmc & self._dmc_mask)
                ]
            )
            * 255
        )

    def toggle_pulse_1(self):
        """
        Toggle audio ouptut on or off for the first pulse channel.
        """
        if self._pulse_1_mask:
            self._pulse_1_mask = 0
        else:
            self._pulse_1_mask = 0xFF

    def toggle_pulse_2(self):
        """
        Toggle audio ouptut on or off for the second pulse channel.
        """
        if self._pulse_2_mask:
            self._pulse_2_mask = 0
        else:
            self._pulse_2_mask = 0xFF

    def toggle_noise(self):
        """
        Toggle audio ouptut on or off for the noise channel.
        """
        if self._noise_mask:
            self._noise_mask = 0
        else:
            self._noise_mask = 0xFF

    def toggle_triangle(self):
        """
        Toggle audio ouptut on or off for the triangle channel.
        """
        if self._triangle_mask:
            self._triangle_mask = 0
        else:
            self._triangle_mask = 0xFF

    def toggle_dmc(self):
        """
        Toggle audio ouptut on or off for the DMC channel.
        """
        if self._dmc_mask:
            self._dmc_mask = 0
        else:
            self._dmc_mask = 0xFF
