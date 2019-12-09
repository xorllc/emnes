# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from unittest import mock
from emnes.apu.noise_shift_register import NoiseShiftRegister


def test_write():
    nsr = NoiseShiftRegister()
    assert nsr.is_short_mode is False
    assert nsr.period == 0x4

    # Setting only the msb turns short mode on
    nsr.write(0x80)
    assert nsr.is_short_mode
    assert nsr.period == 0x4
    nsr.write(0x00)

    # Resetting turns it 0ff
    assert nsr.is_short_mode is False
    assert nsr.period == 0x4

    # Writing middle bits changes nthing
    nsr.write(0b1110000)
    assert nsr.is_short_mode is False
    assert nsr.period == 0x4

    for value in range(0, 16):
        nsr.write(value)
        assert nsr.period == nsr.PERIOD_LOOKUP[value]

    nsr.write(16)
    assert nsr.period == 0x4
    nsr.write(17)
    assert nsr.period == 0x8


def _emulate_4(nsr):
    for _ in range(4):
        nsr.emulate()


def test_long_mode():
    nsr = NoiseShiftRegister(is_short_mode=False)
    assert nsr.shift == 1
    assert nsr.counter == 1
    assert nsr.is_short_mode is False
    # Make sure the counter is of the right value all along
    # and that the shift register is correct.
    # and
    for i in range(4, 0, -1):
        nsr.emulate()
        assert nsr.shift == 1 << 14
        assert nsr.counter == i
    nsr.emulate()

    # We should have wrapped around now and been shifted.
    assert nsr.counter == 4
    assert nsr.shift == 1 << 13
    _emulate_4(nsr)
    assert nsr.shift == 1 << 12

    nsr = NoiseShiftRegister(2, is_short_mode=False)
    _emulate_4(nsr)
    assert nsr.shift == (1 << 14) | 1
    _emulate_4(nsr)
    assert nsr.shift == (0b11 << 13)

    nsr = NoiseShiftRegister(3, is_short_mode=False)
    _emulate_4(nsr)
    assert nsr.shift == 1
    _emulate_4(nsr)
    assert nsr.shift == (1 << 14)
    _emulate_4(nsr)
    assert nsr.shift == (0b1 << 13)


def test_short_mode():
    nsr = NoiseShiftRegister(is_short_mode=True)
    assert nsr.shift == 1
    assert nsr.counter == 1
    assert nsr.is_short_mode
    nsr.emulate()
    assert nsr.shift == 1 << 14
    assert nsr.counter == 4
    nsr.emulate()
    assert nsr.counter == 3
    nsr.emulate()
    assert nsr.counter == 2
    nsr.emulate()
    assert nsr.counter == 1
    nsr.emulate()
    assert nsr.counter == 4
    nsr.emulate()
    assert nsr.shift == 1 << 13
    for _ in range(4):
        nsr.emulate()
    assert nsr.shift == 1 << 12

    nsr = NoiseShiftRegister(0b1000001, is_short_mode=True)
    nsr.emulate()
    assert nsr.shift == 0b100000


def test_output():
    for shift in range(1 << 15):
        nsr = NoiseShiftRegister(shift=shift)
        assert nsr.output == 0 if (shift & 1 == 1) else 1, f"Shift is {shift}"
