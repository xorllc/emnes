# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class Zapper:
    """
    Implements the NES Zapper.

    The NES Zapper, contrary to the gamepad, can always be read and ignores writes.
    When read, It will return whether the trigger is being pressed and if light
    was detected.
    """

    __slots__ = "trigger_pulled _light_detected _aimed_x _aimed_y".split()

    def __init__(self):
        """
        Init.
        """
        self.trigger_pulled = False
        self._light_detected = False
        self._aimed_x = 0
        self._aimed_y = 0

    def update_aim_location(self, x, y):
        """
        Indicates which pixel coordinate the light gun is pointing towards.
        """
        self._aimed_x = x
        self._aimed_y = y

    def update_light_state(self, pixels):
        """
        Updates the state of the light based on the pixel value at the current
        (x, y) coordinates tracked by the gun.

        :param bytearray pixels: Array of pixels to look into. Has 256 * 240 pixels.
        """
        # Reads pixel at x, y.
        color = pixels[self._aimed_y * 256 + self._aimed_x]
        # The light gun reports light on white and shades of gray.
        self._light_detected = color == 0x00 or color == 0x10 or color == 0x20 or color == 0x30

    def write(self, value):
        """
        Can't write to this register.
        """
        pass

    def read(self):
        """
        Returns the state of the zapper.

        :returns: State of the zapper.
        """
        return int(self.trigger_pulled) << 4 | int(not self._light_detected) << 3
