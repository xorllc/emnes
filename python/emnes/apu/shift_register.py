# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class ShiftRegister:

    __slots__ = ("_sample", "_nb_bits_left")

    def __init__(self):
        self._sample = 0
        self._nb_bits_left = 8

    def load_sample(self, sample):
        self._sample = sample
        self._nb_bits_left = 8

    @property
    def bit_0(self):
        return self._sample & 1

    def clock(self):
        if self._sample is not None:
            self._sample >>= 1
        self._nb_bits_left -= 1
        return self._nb_bits_left == 0
