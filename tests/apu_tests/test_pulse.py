# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from unittest import mock
from emnes.apu.pulse import Pulse


def test_active(clockable_pulse):
    assert clockable_pulse.active


def test_update_period(pulse):
    pulse.write_byte(0x4002, 0b10101010)
    pulse.write_byte(0x4003, 0xFF)
    assert pulse.square_wave.waveform_period == 0b11110101010


def test_update_length_counter(pulse):
    pulse.write_byte(0x4003, 0)
    assert pulse.length_counter.value == 0x0A

    pulse.write_byte(0x4003, 0b1000)
    assert pulse.length_counter.value == 0xFE

    pulse.write_byte(0x4003, 0b10000)
    assert pulse.length_counter.value == 0x14

    pulse.write_byte(0x4003, 0b11000)
    assert pulse.length_counter.value == 0x02

    pulse.write_byte(0x4003, 0b1111000)
    assert pulse.length_counter.value == 0x0E

    pulse.write_byte(0x4003, 0b11111000)
    assert pulse.length_counter.value == 0x1E


def test_disable():
    pulse = Pulse(0x4000)
    # Channel is disabled and inactive by default.
    assert pulse.enabled is False
    assert pulse.active is False

    pulse.enabled = True
    assert pulse.enabled is True
    # Enabling it does not initialize the length counter
    assert pulse.active is False


def test_halt_bit(clockable_pulse):
    assert clockable_pulse.length_counter.halted is False
    clockable_pulse.write_byte(0x4000, 0b100000)
    assert clockable_pulse.length_counter.halted is True


def test_disabling_clears_length_counter(clockable_pulse):
    clockable_pulse.enabled = False
    assert clockable_pulse.enabled is False
    assert clockable_pulse.active is False
    assert clockable_pulse.length_counter.value == 0


def test_reloading_when_disabled():
    """
    When the channel is disabled, reloading the length counter
    will do nothing.
    """
    pulse = Pulse(0x4000)
    assert pulse.enabled is False
    pulse.write_byte(0x4003, 0)
    # When disabled, reloading the length counter does not work
    assert pulse.active is False


def test_clocking_enabled(clockable_pulse):
    clockable_pulse
    previous_length_counter = clockable_pulse.length_counter.value
    clockable_pulse.clock_length_counter()
    assert clockable_pulse.length_counter.value == previous_length_counter - 1
