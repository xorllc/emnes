# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class MemoryBus:
    """
    This class routes read/writes from the CPU to the right device.
    """

    def __init__(self, cartridge, ppu, input_device_1, input_device_2):
        """
        :param emnes.Cartridge cartridge: Cartridge that is was loaded into the emulator.
        """
        self._cartridge = cartridge
        self._ram = bytearray(0x800)
        self._ppu = ppu
        self._ppu.memory_bus = self
        self._memory_reg = bytearray(0x20)
        self._input_device_1 = input_device_1
        self._input_device_2 = input_device_2

    def _set_cpu(self, cpu):
        self._cpu = cpu

    cpu = property(None, _set_cpu)

    def read_byte(self, addr):
        """
        Read a byte from memory.

        :param int addr: Address to read a byte from.

        :returns: The byte that was read.
        """
        # Test for the two most common memory regions first.
        if addr >= 0x8000:
            return self._cartridge.read_rom_byte(addr - 0x8000)
        elif addr < 0x2000:
            addr &= 0x7FF
            return self._ram[addr]
        elif addr >= 0x6000:
            return self._cartridge.read_sram_byte(addr - 0x6000)
        elif addr >= 0x4020:
            self._not_implemented("Expansion ROM (0x4020-0x6000)", addr, is_read=True)
        elif addr >= 0x4000:
            if addr == 0x4016:
                return self._input_device_1.read()
            elif addr == 0x4017:
                return self._input_device_2.read()
            return self._memory_reg[addr - 0x4000]
        elif addr >= 0x2000:
            return self._ppu.read_byte(addr & 0x2007)
        else:
            raise RuntimeError(f"Unexpected memory read {hex(addr)}")

    def read_array(self, addr, length):
        """
        Read a array of bytes from memory.

        :param int addr: Address to read a bytes from.
        :param int length: Number of bytes to read.

        :returns: The bytes that were read.
        """
        result = bytearray(length)
        for i in range(length):
            result[i] = self.read_byte(i + addr)
        return result

    def write_byte(self, addr, value):
        """
        Write a byte to memory.

        :param int addr: Address to write a byte to.
        :param int value: Value of the byte to write.
        """
        # Test for the two most common memory regions first.
        if addr >= 0x8000:
            self._cartridge.write_rom_byte(addr - 0x8000, value)
        elif addr < 0x2000:
            addr &= 0x7FF
            self._ram[addr] = value
        elif addr >= 0x6000:
            self._cartridge.write_sram_byte(addr - 0x6000, value)
        elif addr >= 0x4020:
            self._not_implemented("Expansion ROM (0x4020-0x6000)", addr, is_read=False)
        elif addr >= 0x4000:
            if addr == 0x4014:
                self._cpu.dma_transfer(value)
            elif addr == 0x4016:
                self._input_device_1.write(value)
            elif addr == 0x4017:
                self._input_device_2.write(value)
            else:
                self._memory_reg[addr - 0x4000] = value
        elif addr >= 0x2000:
            self._ppu.write_byte(addr & 0x2007, value)
        else:
            raise RuntimeError(f"Unexpected memory write at {hex(addr)}")

    def _not_implemented(self, region, addr, is_read):
        """
        Raise an NotImplementedError formatted according to the parameter.

        :param str region: Name of the region that is not implemented.
        :param int addr: Address that was accessed.
        :param boolean is_read: If True, the operation was a read.

        :raises NotImplementedError: Always raised with a string matching the parameters.
        """
        raise NotImplementedError(
            f"{region} {'read' if is_read else 'write'} at {hex(addr)} not implemented."
        )
