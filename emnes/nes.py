# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.cartridge_reader import CartridgeReader
from emnes.memory_bus import MemoryBus
from emnes.cpu import CPU
from emnes.ppu import PPU
from emnes.mirroring_type import MirroringType


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
        self._ppu = None
        self._cpu = None
        self._frame_ready = False

    def load_rom(self, path_to_rom):
        """
        Load a rom into the emulator.

        Only the .nes format is supported.

        :param str path_to_rom: Path to the ROM file to load.

        :raises Exception: Yeah!
        """
        self._cartridge = CartridgeReader.load_from_disk(path_to_rom)
        self.power()

    def _set_frame_ready(self):
        """
        Sets the _frame_ready flag.
        """
        self._frame_ready = True

    def is_frame_ready(self):
        """
        Indicates if the PPU is done rendering a frame.
        """
        return self._frame_ready

    def power(self):
        """
        Set the console in its initial state.
        """
        self._cartridge.power()
        # TODO: There's a bit of circular dependency here, we should look into
        # fixing it.
        # CPU -> MemoryBus -> PPU -> CPU
        self._ppu = PPU(self._set_frame_ready)
        self._cartridge.configure(self._ppu)

        assert self._cartridge.mirroring_type in [MirroringType.Horizontal, MirroringType.Vertical]
        # Horizontal mapping maps ppu nametable addresses:
        # - 0x2400 to 0x2000
        # - 0x2C00 to 0x2800
        # Horizontal mapping maps ppu nametable addresses:
        # - 0x2800 to 0x2000
        # - 0x2C00 to 0x2400
        self._ppu.set_mirroring_options(
            0xF7FF if self._cartridge.mirroring_type == MirroringType.Vertical else 0xFBFF
        )

        self._memory_bus = MemoryBus(self._cartridge, self._ppu)
        self._cpu = CPU(self._ppu, self._memory_bus)

    def reset(self):
        """
        Reset the console.
        """
        self._cpu.reset()

    def emulate_once(self):
        """
        Emulate one instruction.
        """
        # TODO: We should try to expose the contents of cpu.emulate_once
        # into the scope of this method. It would remove millions of function
        # calls per second. It is the second most invoked method.
        # PPU.emulate_once is the most invoked, PPU._render_pixel is the third.
        cycles_before = self._cpu.nb_cycles
        self._frame_ready = False
        self._cpu.emulate()
        for i in range(self._cpu.nb_cycles - cycles_before):
            self._ppu.emulate_once()
            self._ppu.emulate_once()
            self._ppu.emulate_once()

    def emulate(self):
        """
        Emulates until the emulator has rendered a complete frame.
        """
        self._frame_ready = False
        while not self._frame_ready:
            cycles_before = self._cpu.nb_cycles
            self._cpu.emulate()
            # The correct way to emulate PPU cycles would be to emulate
            # them after each CPU tick. Unfortunately, this seems like an inefficient
            # way of doing things and the performance is much much slower.
            #
            # Instead, we'll count many cycles have passed during the instruction
            # and then emulate the PPU accordingly. This isn't as precise
            # as the real hardware, but it's hopefully a good balance between
            # accuracy and speed for a Python based interpreter.
            for i in range(self._cpu.nb_cycles - cycles_before):
                self._ppu.emulate_once()
                self._ppu.emulate_once()
                self._ppu.emulate_once()

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

    @property
    def ppu(self):
        """
        Access the PPU.
        """
        return self._ppu
