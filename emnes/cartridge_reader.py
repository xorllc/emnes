# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.mirroring_type import MirroringType
from emnes.readers.cartridge_header import CartridgeHeader
from emnes.mappers import MapperRegistry


class CartridgeReader:
    """
    Allows to manipulate cartridge data. Only supports the .nes format.
    """

    @classmethod
    def load_from_disk(cls, path_to_rom):
        """
        Load a cartridge data from disk

        :param str path_to_rom: Path to the ROM to load.

        :returns: An instance of :class:`Cartridge`
        """
        with open(path_to_rom, "rb") as fh:
            return cls.load_from_data(fh.read())

    @classmethod
    def load_from_data(cls, cart_data):
        """
        Load a cartridge from an array of bytes.

        :param bytearray cart_data:

        :returns: A :class:`MapperBase` derived object.
        """
        nes_string = cart_data[0:4]

        # iNES rom format should start with NES
        if nes_string != b"NES\x1a":
            raise RuntimeError("Emulator only supports ROMs in the iNes format.")

        nb_rom_banks = cart_data[4]
        nb_vrom_banks = cart_data[5]
        is_battery_backed = True if cart_data[6] & 2 else False
        has_trainer = True if cart_data[6] & 4 else False

        rom_control_byte_1 = cart_data[6]

        if rom_control_byte_1 & (1 << 3):
            mirroring_type = MirroringType.FourScreen
        elif rom_control_byte_1 & 1:
            mirroring_type = MirroringType.Vertical
        else:
            mirroring_type = MirroringType.Horizontal

        rom_control_byte_2 = cart_data[7]

        mapper_number = (rom_control_byte_1 >> 4) | (rom_control_byte_2 & 0b11110000)

        nb_sram_banks = cart_data[8]
        if nb_sram_banks == 0:
            nb_sram_banks = 1

        rom_data_start = 16 + (512 if has_trainer else 0)
        rom_data_end = rom_data_start + 16 * 1024 * nb_rom_banks

        assert rom_data_end <= len(cart_data)

        header = CartridgeHeader(
            nb_rom_banks,
            nb_vrom_banks,
            is_battery_backed,
            has_trainer,
            mirroring_type,
            nb_sram_banks,
        )

        rom = cart_data[rom_data_start:rom_data_end]

        mapper = MapperRegistry.create_mapper(mapper_number, header, rom)

        return mapper
