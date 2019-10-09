# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.mappers.mmc1 import MMC1
from emnes.mappers.nrom_switch import NROMSwitch


class MapperRegistry:
    """
    Registry of mappers.

    Allows to instantiate a mapper.
    """

    _mapper_registry = {0: NROMSwitch, 1: MMC1}

    @classmethod
    def create_mapper(cls, mapper_number, header, cart_data):
        """
        Create a mapper based on a mapper number, header information and ROM data.

        :param int mapper_number: Mapper number that corresponds to one of the
            supported mapper types.
        :param emnes.readers.CartridgeHeader header: Cartridge information.
        :param bytearray cart_data: Bytes from the cartridge.

        :returns: Instance of a :class:`emnes.mappers.MemoryBase` derived class.
        """
        if mapper_number not in cls._mapper_registry:
            raise NotImplementedError(f"Mapper {mapper_number} is not implemented.")
        return cls._mapper_registry[mapper_number](header, cart_data)
