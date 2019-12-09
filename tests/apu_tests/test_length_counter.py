# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.apu.length_counter import LengthCounter


def test_default_state():
    """
    Tests the default state.
    """
    lc = LengthCounter()
    assert lc.value == 0
    assert lc.halted is False


def test_reload():
    """
    Ensure reload read the lookup table properly
    or sets to zero when set to None.
    """
    lc = LengthCounter()
    lc.reload(0)
    assert lc.value == 0x0A
    lc.reload(31)
    assert lc.value == 0x1E
    lc.reload(None)
    assert lc.value == 0
    lc.halted = True
    lc.reload(0)
    assert lc.value == 0x0A


def test_halted():
    """
    Ensure halting the counter disables clocking.
    """
    lc = LengthCounter()
    lc.reload(0)
    lc.clock()
    assert lc.value == 0x9
    lc.halted = True
    lc.clock()
    assert lc.value == 0x9


def test_active():
    """
    Ensure active returns true when the length counter value is non-zero.
    """
    lc = LengthCounter()
    assert lc.active is False
    lc.reload(0)
    assert lc.active
    lc.halted = True
    assert lc.active
    lc.reload(None)
    assert lc.active is False


def test_clock():
    """
    Ensure clock decreases the current counter unless never does below zero.
    """
    lc = LengthCounter()
    lc.reload(0)
    assert lc.value == 0x0A
    for i in range(9, -1, -1):
        lc.clock()
        assert lc.value == i
    assert lc.value == 0
    lc.clock()
    assert lc.value == 0
