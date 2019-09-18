# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class Gamepad:
    """
    Implements the NES gamepad.

    The NES gamepad is super easy to emulate. When writing 1 to the register,
    it starts reading the controller input. When 0 is set, the state is
    copied to the register and the register can be read one bit at a time.
    As the register is read, the bits are shifted inside the register.
    The state can be read one bit at a time, 8 times. The button states will be
    read in that order:
    - A
    - B
    - Select
    - Start
    - Up
    - Down
    - Left
    - Right.
    """

    __slots__ = "a b up down left right select start _buffer _read_mode".split()

    def __init__(self):
        """
        Init.
        """
        # TODO: Implement some logic that prevents from pressing opposite directions
        # at the same time on the same controller.
        self.a = False
        self.b = False
        self.up = False
        self.down = False
        self.left = False
        self.right = False
        self.select = False
        self.start = False
        self._buffer = 0
        self._read_mode = True

    def write(self, value):
        """
        Starts and stop button state refresh.

        :param int value: If 1, starts refreshing the gamepad state. If 0, refresh
            is stopped and the read method will start returning the controller
            state one bit at a time.
        """
        self._buffer = (
            int(self.a) << 7
            | int(self.b) << 6
            | int(self.select) << 5
            | int(self.start) << 4
            | int(self.up) << 3
            | int(self.down) << 2
            | int(self.left) << 1
            | int(self.right)
        )
        self._read_mode = value == 0

    def read(self):
        """
        Returns the state of the buttons.

        If last write was 0, each rid will return the state of a different button until
        all 8 have been read.

        If last write was 1, the state of the A button will constantly be returned.

        :returns: True if the next button state is pressed, False otherwise.
        """
        button_pressed = self._buffer >> 7
        if self._read_mode:
            self._buffer = (self._buffer << 1) & 0xFF
        return button_pressed
