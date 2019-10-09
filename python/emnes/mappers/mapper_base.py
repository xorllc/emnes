# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

import os


class MapperBase:
    """
    Base class for cartridge memory mappers.
    """

    __slots__ = [
        # NES cartridges are responsible for providing memory for the pattern memory
        # table of the NES. Some provide a simple R/W memory that the game can
        # write to and others will provide bankable VROM. When the memory is
        # r/w, it means that it's state will need to be persisted everytime we save the
        # state of the emulator.
        "_has_rw_vrom",
        "_rom",
        "_vrom",
        "_sram",
        "_path",
        "_nb_rom_banks",
        "_nb_vrom_banks",
        "_is_battery_backed",
        "_has_trainer",
        "_mirroring_type",
        "_nb_sram_banks",
        # Whenever the console needs to switch VROM memory bank, it will
        # invoke this method to update the PPU.
        "_vrom_switch_handler",
    ]

    def __init__(self, header, data):
        """
        :param emnes.readers.CartridgeHeader header: Cartridge header.
        """
        self._has_rw_vrom = False
        self._sram = bytearray(header.nb_sram_banks * 8 * 1024)
        self._path = header.path
        self._nb_rom_banks = header.nb_rom_banks
        self._nb_vrom_banks = header.nb_vrom_banks
        self._is_battery_backed = header.is_battery_backed
        self._has_trainer = header.has_trainer
        self._mirroring_type = header.mirroring_type
        self._nb_sram_banks = header.nb_sram_banks
        self._set_rom_and_vrom(data)

    def set_handlers(self, vrom_switch_handler):
        """
        Sets the handlers required to update the other
        parts of the NES when some state change inside the
        mapper.
        """
        self._vrom_switch_handler = vrom_switch_handler

    def __getstate__(self):
        """
        Captures the state of the mapper. Used when pickling.

        :returns: `dict` of the state.
        """
        state = {}
        # For some reason __slots__ only contains the slots from the
        # derived class, so we need to use Mapper.__slots__ as well...
        for k in self.__slots__ + MapperBase.__slots__:
            # We don't want to pickle the ROM data, so skip those.
            if k in ["_rom"] + ["_vrom"] if self._has_rw_vrom is False else []:
                continue
            state[k] = getattr(self, k)
        return state

    def __setstate__(self, state):
        """
        Restores the state of the mapper. Used when unpickling.

        :param dict state: State captured by __getstate__.
        """
        for k, v in state.items():
            setattr(self, k, v)

        # FIXME: We've got ourselves a circular dependency problem here...
        from emnes.cartridge_reader import CartridgeReader

        # We didn't pickle ROM data, so reload it.
        with open(self._path, "rb") as f:
            _, _, data = CartridgeReader.get_cart_sections(f.read(), self._path)

        self._set_rom_and_vrom(data)
        # Set back the memory for the PPU. It didn't save it's
        # pattern memory either.
        self._vrom_switch_handler(self._vrom)

    def _set_rom_and_vrom(self, data):
        """
        Splits data from the cartridge into ROM and VROM data.

        :param bytes data: Data from the cartridge.
        """
        vrom_start = self.nb_rom_banks * 16 * 1024
        self._rom = data[:vrom_start]
        if self._has_rw_vrom is False:
            self._vrom = data[vrom_start:]

    @property
    def name(self):
        """
        The name of the ROM, minus the folder location.
        """
        return os.path.basename(self._path)

    def power(self):
        """
        Reset the content of SRAM is the RAM is not battery backed.
        """
        if self._is_battery_backed is False:
            for i in range(len(self._sram)):
                # TODO: Pass in garbage in here.
                self._sram[i] = 0

    def configure(self):
        """
        Implemented by the derived classes so that they can configure PPU
        options. Default implementation provides RW memory for the
        console to use.
        """
        self._has_rw_vrom = True
        self._vrom = bytearray(0x2000)
        self._vrom_switch_handler(self._vrom)

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
