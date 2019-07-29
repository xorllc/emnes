# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class CartridgeHeader:
    """
    Contains information about the cartridge.
    """

    __slots__ = [
        "_nb_rom_banks",
        "_nb_vrom_banks",
        "_is_battery_backed",
        "_has_trainer",
        "_mirroring_type",
        "_nb_sram_banks",
    ]

    def __init__(
        self,
        nb_rom_banks,
        nb_vrom_banks,
        is_battery_backed,
        has_trainer,
        mirroring_type,
        nb_sram_banks,
    ):
        r"""
        :param int nb_rom_banks: Number of ROM banks in the cartridge.
        :param int nb_vrom_banks: Number of VROM banks in the cartridge.
        :param bool is_battery_backed: True is the SRAM persists between power cycles.
        :param bool has_trainer: ¯\_(ツ)_/¯
        :param emnes.mirroring_type.MirroringType: Mirroring-type used in PPU.
            For cartridge with hard-wired mirroring.
        :param int nb_sram_banks: Number of SRAM banks in the cartridge.
        """
        self._nb_rom_banks = nb_rom_banks
        self._nb_vrom_banks = nb_vrom_banks
        self._is_battery_backed = is_battery_backed
        self._has_trainer = has_trainer
        self._mirroring_type = mirroring_type
        self._nb_sram_banks = nb_sram_banks

    @property
    def nb_rom_banks(self):
        """
        The number of rom banks in the cartridge
        """
        return self._nb_rom_banks

    @property
    def nb_vrom_banks(self):
        """
        The number of vrom banks in the catridge.
        """
        return self._nb_vrom_banks

    @property
    def is_battery_backed(self):
        """
        Is there a battery for save games?
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
