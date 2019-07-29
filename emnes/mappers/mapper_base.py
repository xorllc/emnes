# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class MapperBase:
    """
    Base class for cartridge memory mappers.
    """

    __slots__ = [
        "_sram",
        "_nb_rom_banks",
        "_nb_vrom_banks",
        "_is_battery_backed",
        "_has_trainer",
        "_mirroring_type",
        "_nb_sram_banks",
    ]

    def __init__(self, header):
        """
        :param emnes.readers.CartridgeHeader header: Cartridge header.
        """
        self._sram = bytearray(header.nb_sram_banks * 8 * 1024)
        self._nb_rom_banks = header.nb_rom_banks
        self._nb_vrom_banks = header.nb_vrom_banks
        self._is_battery_backed = header.is_battery_backed
        self._has_trainer = header.has_trainer
        self._mirroring_type = header.mirroring_type
        self._nb_sram_banks = header.nb_sram_banks

    def power(self):
        """
        Reset the content of SRAM is the RAM is not battery backed.
        """
        if self._is_battery_backed is False:
            for i in range(len(self._sram)):
                # Not accurate, as there probably should be garbage in there.
                self._sram[i] = 0

    def read_sram_byte(self, addr):
        """
        Read an SRAM byte.

        :param int addr: Address to read an SRAM byte from.
        """
        return self._sram[addr]

    def write_sram_byte(self, addr, value):
        """
        Write a byte to SRAM.

        :param int addr: Address to write a byte at.
        :param int value: Value to write.
        """
        self._sram[addr] = value

    @property
    def nb_rom_banks(self):
        """
        Number of ROM banks in the cartridge
        """
        return self._nb_rom_banks

    @property
    def nb_vrom_banks(self):
        """
        Number of VROM banks in the catridge.
        """
        return self._nb_vrom_banks

    @property
    def is_battery_backed(self):
        """
        If there a battery for save games.
        """
        return self._is_battery_backed

    @property
    def has_trainer(self):
        """
        No clue what a trainer is to be honest!
        """
        return self._has_trainer

    @property
    def mirroring_type(self):
        """
        Dunno!
        """
        return self._mirroring_type

    @property
    def nb_sram_banks(self):
        """
        Number of SRAM banks.
        """
        return self._nb_sram_banks

    @property
    def expected_rom_size(self):
        """
        Compute the expected file size based on the number of rom, sram and vrom banks.

        :returns: The size of the ROM in bytes.
        """
        return (
            (self.nb_rom_banks * 16 + self.nb_vrom_banks * 8) * 1024
            + (512 if self.has_trainer else 0)
            + 16
        )
