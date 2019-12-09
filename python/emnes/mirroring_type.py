# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

import enum


class MirroringType(enum.IntEnum):
    """
    Mirroring type used in a cartridge that has hard-wired mirroring.

    This is used by the :class:`CartridgeHeader` class.
    """

    OneScreenLower = 0
    OneScreenUpper = 1
    Horizontal = 2
    Vertical = 3

    def __format__(self, format_spec):
        """
        Format the value into a string.

        The format specifier does not do anything.

        :param str format_spec: Format specifier. Unused.
        """
        if self.value == self.Horizontal:
            return "horizontal"
        elif self.value == self.Vertical:
            return "vertical"
        elif self.value == self.OneScreenUpper:
            return "one screen (upper)"
        elif self.value == self.OneScreenLower:
            return "one screen (lower)"
        else:
            raise RuntimeError(f"Unexpected mirroring value: {self.value}")
