# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.cartridge_reader import CartridgeReader
from emnes.memory_bus import MemoryBus
from emnes.cpu import CPU


class NES:
    """
    Emulator for the NES.

    Instantiating this class will provide an emulated Nintendo. To use it,
    you must first provide a path to a rom via the load_rom method. After that,
    you can call the emulate method to emulate the console.

    You can reset the emulator by calling reset.
    """

    def __init__(self):
        """
        Init
        """
        self._cartridge = None
        self._memory_bus = None
        self._cpu = None

    def load_rom(self, path_to_rom):
        """
        Load a rom into the emulator.

        Only the .nes format is supported.

        :param str path_to_rom: Path to the ROM file to load.

        :raises Exception: Yeah!
        """
        self._cartridge = CartridgeReader.load_from_disk(path_to_rom)
        self.power()

    def power(self):
        """
        Set the console in its initial state.
        """
        self._cartridge.power()
        self._memory_bus = MemoryBus(self._cartridge)
        self._cpu = CPU(self._memory_bus)
        self.reset()

    def reset(self):
        """
        Reset the console.
        """
        self._cpu.reset()

    def emulate(self):
        """
        Emulate one instruction.
        """
        self._cpu.emulate()

    @property
    def cartridge(self):
        """
        Cartridge loaded in the emulator.
        """
        return self._cartridge

    @property
    def memory_bus(self):
        """
        Memory bus allowing to communicate with the different components.
        """
        return self._memory_bus

    @property
    def cpu(self):
        """
        Access the CPU.
        """
        return self._cpu
