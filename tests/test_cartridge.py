# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

import pytest

from emnes import CartridgeReader
from emnes.mirroring_type import MirroringType


CART_DATA_TEMPLATE = (
    # 4 bytes Header
    b"NES"
    + bytes.fromhex("1A")
    # 15 PRG ROM banks
    + bytes.fromhex("0F")
    # 3 CHR ROM/VROM banks
    + bytes.fromhex("03")
    # rom control 1&2 and nb ram banks
    + bytes.fromhex("000000")
    # Pad an extra megabyte just so the cart is big enough for the test.
    + bytes(0 for i in range(1024 * 1024))
)


def test_valid_headers():
    """
    Check valid header works.
    """
    CartridgeReader.load_from_data(CART_DATA_TEMPLATE)


def test_invalid_headers():
    """
    Check header without NES or 0x1A at the beginning fail.
    """
    with pytest.raises(RuntimeError) as exinfo:
        CartridgeReader.load_from_data(b"GBA" + bytes.fromhex("1A"))

    assert str(exinfo.value).startswith("Emulator only supports ROMs in the iNes format.")

    with pytest.raises(RuntimeError) as exinfo:
        CartridgeReader.load_from_data(b"NES" + bytes.fromhex("00"))

    assert str(exinfo.value).startswith("Emulator only supports ROMs in the iNes format.")


def test_nb_banks():
    """
    Test reading number of rom banks.
    """
    assert CartridgeReader.load_from_data(CART_DATA_TEMPLATE).nb_rom_banks == 15
    assert CartridgeReader.load_from_data(CART_DATA_TEMPLATE).nb_vrom_banks == 3


def test_battery_flag():
    """
    Test reading battery flag.
    """
    assert CartridgeReader.load_from_data(CART_DATA_TEMPLATE).is_battery_backed is False

    # Set battery backed bit.
    data = bytearray(CART_DATA_TEMPLATE)
    data[6] = 0b10
    assert CartridgeReader.load_from_data(data).is_battery_backed is True


def test_trainer_flag():
    """
    Test trainer flag.
    """
    assert CartridgeReader.load_from_data(CART_DATA_TEMPLATE).has_trainer is False
    data = bytearray(CART_DATA_TEMPLATE)

    # Set trainer bit
    data[6] = 0b100
    assert CartridgeReader.load_from_data(data).has_trainer is True


def test_mirroring_flags():
    """
    Test mirroring flags.
    """
    data = bytearray(CART_DATA_TEMPLATE)
    # Set the different mirroing types.
    data[6] = 0
    assert CartridgeReader.load_from_data(data).mirroring_type == MirroringType.Horizontal

    data[6] = 1
    assert CartridgeReader.load_from_data(data).mirroring_type == MirroringType.Vertical

    # Set both vertical and four screen mirroring, four screen should
    # always take precedence.
    data[6] = 0b1001
    assert CartridgeReader.load_from_data(data).mirroring_type == MirroringType.FourScreen


def test_mapper_detection():
    """
    Test mapper detection.
    """
    data = bytearray(CART_DATA_TEMPLATE)
    # Four upper bits is lower bits of mapper number
    data[6] = 0b10011111
    # Four upper bits is higher bits of mapper number
    data[7] = 0b11000000

    expected_mapper = 0b11001001
    with pytest.raises(NotImplementedError) as exinfo:
        assert CartridgeReader.load_from_data(data).mapper_number == expected_mapper

    assert str(exinfo.value) == "Mapper 201 is not implemented."
