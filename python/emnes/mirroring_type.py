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

    Horizontal = 0
    Vertical = 1
    FourScreen = 2

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
        else:
            return "four screen"
