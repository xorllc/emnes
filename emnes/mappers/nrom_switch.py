# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.mappers.mapper_base import MapperBase


class NROMSwitch(MapperBase):
    """
    NROM Switch Memory mapper.

    Supports:
    - 16k of memory mapped twice
    - 32kb of memory mapped once
    """

    __slots__ = ["_rom", "_vrom", "_address_mask"]

    def __init__(self, header, data):
        """
        :param emnes.CartridgeHeader header: Header for the cartridge.
        :param bytearray data: Cartridge data
        """
        super().__init__(header)
        # If there is only one bank, the higher area
        # will simply mirror data in the lower area.
        # as such, we're only concerned with the first 0x3FFF

        if header.nb_rom_banks == 1:
            self._address_mask = 0x3FFF
            vrom_start = 16 * 1024
        else:
            self._address_mask = 0xFFFF
            vrom_start = 32 * 1024

        self._rom = data[:vrom_start]
        self._vrom = data[vrom_start:]

    def configure(self, ppu):
        """
        Configures the PPU for reading the video rom memory.
        """
        # FIXME: Incredibly naive. The VROM is bankable, so will not work for lots of games.
        if self._vrom:
            ppu.configure(self._vrom)

    def write_rom_byte(self, addr, data):
        """
        Does not do anything. ROM switching is not supported for this ROM type.
        """
        raise NotImplementedError(
            f"Write (addr: {hex(addr)}, value: {hex(data)}) not supported in NROM."
        )

    def read_rom_byte(self, addr):
        """
        Read a rom byte.

        :param int addr: Address of the byte to read.

        :returns: The read byte.
        """
        return self._rom[addr & self._address_mask]
