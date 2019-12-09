# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from unittest.mock import Mock
import pytest

from unittest import mock
from emnes.apu.status import Status
from emnes.apu.pulse import Pulse
from emnes.apu.triangle import Triangle
from emnes.apu.noise import Noise
from emnes.apu.dmc import DMC


@pytest.fixture
def pulse_4000():
    pulse = Pulse(0x4000)
    pulse.enabled = True
    # This will load the period at index 0 in the table,
    # making it active.
    pulse.write_byte(0x4003, 0)
    return pulse


@pytest.fixture
def pulse_4004():
    pulse = Pulse(0x4004)
    pulse.enabled = True
    # This will load the period at index 0 in the table,
    # making it active.
    pulse.write_byte(0x4007, 0)
    return pulse


@pytest.fixture
def triangle():
    triangle = Triangle()
    triangle.enabled = True
    # This will load the period at index 0 in the table,
    # making it active.
    triangle.write_byte(0x400B, 0)
    return triangle


@pytest.fixture
def noise():
    noise = Noise()
    noise.enabled = True
    # This will load the period at index 0 in the table,
    # making it active.
    noise.write_byte(0x400F, 0)
    return noise


@pytest.fixture
def dmc():
    memory_bus_mock = Mock()
    memory_bus_mock.read_byte.return_value = 9
    dmc = DMC(memory_bus_mock)
    dmc.dma_reader.start_address = 0x8000
    dmc.dma_reader.length = 2
    # Selects a non looping period of 54 cycles
    dmc.write_byte(0x4010, 0xF)
    assert dmc.dma_reader.bytes_remaining == 0
    return dmc


@pytest.fixture
def status(pulse_4000, pulse_4004, triangle, noise, dmc):
    return Status(pulse_4000, pulse_4004, triangle, noise, dmc)


def test_status_all_enabled(status):
    assert status.read_byte() == 15


def test_status_disable_pulse_4000(status, pulse_4000, pulse_4004, triangle, noise, dmc):
    status.write_byte(0b11111110)
    assert pulse_4000.enabled is False
    assert pulse_4004.enabled is True
    assert triangle.enabled is True
    assert noise.enabled is True
    # DMA does not have an enabled flag, but
    # when enabled it reloads the dma_reader
    assert dmc.dma_reader.bytes_remaining == 2
    assert status.read_byte() == 30


def test_status_disable_pulse_4004(status, pulse_4000, pulse_4004, triangle, noise, dmc):
    status.write_byte(0b11111101)
    assert pulse_4000.enabled is True
    assert pulse_4004.enabled is False
    assert triangle.enabled is True
    assert noise.enabled is True
    # DMA does not have an enabled flag, but
    # when enabled it reloads the dma_reader
    assert dmc.dma_reader.bytes_remaining == 2
    assert status.read_byte() == 29


def test_status_disable_triangle(status, pulse_4000, pulse_4004, triangle, noise, dmc):
    status.write_byte(0b11111011)
    assert pulse_4000.enabled is True
    assert pulse_4004.enabled is True
    assert triangle.enabled is False
    assert noise.enabled is True
    # DMA does not have an enabled flag, but
    # when enabled it reloads the dma_reader
    assert dmc.dma_reader.bytes_remaining == 2
    assert status.read_byte() == 27


def test_status_disable_noise(status, pulse_4000, pulse_4004, triangle, noise, dmc):
    status.write_byte(0b11110111)
    assert pulse_4000.enabled is True
    assert pulse_4004.enabled is True
    assert triangle.enabled is True
    assert noise.enabled is False
    # DMA does not have an enabled flag, but
    # when enabled it reloads the dma_reader
    assert dmc.dma_reader.bytes_remaining == 2
    assert status.read_byte() == 23


def test_status_disable_dmc(status, pulse_4000, pulse_4004, triangle, noise, dmc):
    status.write_byte(0b11101111)
    assert pulse_4000.enabled is True
    assert pulse_4004.enabled is True
    assert triangle.enabled is True
    assert noise.enabled is True
    # DMA does not have an enabled flag, but
    # when enabled it reloads the dma_reader
    assert dmc.dma_reader.bytes_remaining == 0
    assert status.read_byte() == 15
