# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.mappers.mapper_base import MapperBase


class MMC1(MapperBase):
    """
    MMC1 Memory controller. Supports:

    - bank switching
    - 16kb/32kb banks
    - sram
    - battery.
    """

    __slots__ = [
        "_8000_bank_offset",
        "_C000_bank_offset",
        # We can only write to a single register at a time, one bit at a
        # time.
        "_register_value",
        "_is_low_pgrom_switching",
        "_is_16kb_switching",
    ]

    def __init__(self, header, data):
        """
        :param emnes.readers.CartridgeHeader header: Header information for the
            cartridge.
        :param bytearray: ROM data.
        """
        super().__init__(header, data)

        self._register_value = 0b10000
        self._is_16kb_switching = False

        # By default, the lower area points to the first bank...
        self._8000_bank_offset = 0
        # ... and the higher area points to the last bank.
        # Note that we're going to substract 0x4000 from the bank
        # so we don't have to remove 0x4000 of the address every single time.
        self._C000_bank_offset = ((header.nb_rom_banks - 1) * 16 * 1024) - 0x4000

    def write_rom_byte(self, addr, value):
        """
        Write a byte into ROM.

        This does not actually update a ROM byte, but allows for bank switching.
        """
        # The addressable ROM is split into 4 memory registers. Writing to anywhere
        # inside a region means writing to that specific register. The regions
        # are
        # 0x0000 - 0x1FFFF, 0x2000 - 0x3FFFF, 0x4000 - 0x5FFFF and 0x6000 - 07FFF.
        # This will move the two most significant bits to the two least significant
        # bits and find which register 0 to 3 we're writing to.
        register = addr >> 13

        # Writing bit 7 resets the register and count.
        if bool(value & 0x80):
            self._register_value = 0b10000
            return

        # The register is initialized with 0b10000 and is 5 bits long. Each time
        # a write happens, the contents is shifted by one on the right and the
        # LSB of 'value' is inserted at bit 4. When the mapper detects that
        # the the lsb of the register is set to 1, then it know that this is
        # the final write and it then needs to read the result and remap memory/
        is_final_write = bool(self._register_value & 0x1)

        bit_to_set = value & 0x1

        # Shifts everything right and inserts the bit
        self._register_value = (self._register_value >> 1) | (bit_to_set << 4)

        # If this was not the last write, we're done.
        if is_final_write is False:
            return

        # This was the final write, so update the right register accordingly
        # This controls a bunch of options for now. Later it will need to
        # be augmented to support CHROM swapping.
        if register == 0:
            # FIXME:
            # Mirroring should probably be computed per read/write based on the
            # nametable base address.
            # So when 2400 is the base, we should mirror read/write to 2000 back unto 2400 if
            # horizontal
            self._mirroring_handler(0xF7FF if (0b11 & self._register_value) == 2 else 0xFBFF)
            self._is_low_pgrom_switching = bool(self._register_value & 0x4)
            self._is_16kb_switching = bool(self._register_value & 0x8)
        elif register == 1 or register == 2:
            # assert self._register_value == 0
            # print(f"{register} = {self._register_value}")
            pass
        elif register == 3:
            bank_number = self._register_value & 0xF
            if self._is_16kb_switching:
                bank_offset = bank_number * 16 * 1024
                if self._is_low_pgrom_switching:
                    self._8000_bank_offset = bank_offset
                else:
                    # We're going to be indexing this via the
                    # addr as it was passed in, so remove 0x04000
                    # so that passing in addr 0x4000 will read byte
                    # 0 of the bank.
                    self._C000_bank_offset = bank_offset - 0x4000
            else:
                # On a 32kb bank switch, bits 1-3 are read to index,
                # so shift right to get the correct bank index.
                # Then we'll compute the base address of each
                # mapped bank, which will be contiguous 16kb blocks.
                bank_number >>= 1
                self._8000_bank_offset = bank_number * 32 * 1024
                # Here there's no need to remove 0x4000 from the address
                # because the memory is contiguous.
                self._C000_bank_offset = bank_number * 32 * 1024
        self._register_value = 0b10000

    def read_rom_byte(self, addr):
        """
        Read a ROM byte.

        :param int addr: Address to read.

        :returns: The byte read.
        """
        # TODO: Change this if for a array indexing with bool(0x4000). See
        # if that makes the code any faster. This is unlikely however,
        # because using [] involves a function call, which is a lot slower
        # than an IF + a comparison in Python.
        if addr >= 0x4000:
            return self._rom[self._C000_bank_offset + addr]
        else:
            return self._rom[self._8000_bank_offset + addr]
