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
from emnes.apu import APU
from emnes.mirroring_type import MirroringType
from emnes.gamepad import Gamepad
from emnes.zapper import Zapper


class NES:
    """
    Emulator for the NES.

    Instantiating this class will provide an emulated Nintendo. To use it,
    you must first provide a path to a rom via the load_rom method. After that,
    you can call the emulate method to emulate the console.

    You can reset the emulator by calling reset.

    A gamepad is connected to port 1 and the zapper to port 2. This is
    not configurable at the moment.
    """

    def __init__(self):
        """
        Init
        """
        self._cartridge = None
        self._memory_bus = None
        self._ppu = None
        self._cpu = None
        self._apu = None
        # Flag raised when the emulation pauses because a new frame has been rendered.
        self._frame_ready = False
        # Flag raised when the emulation pauses to request an update to the controller
        # inputs.
        self._input_requested = False
        # Counts how many cycles since the emulation was paused to update the
        # controller status.
        self._cycles_since_last_controller_poll = 0

        self._gamepad = Gamepad()
        self._zapper = Zapper()

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

    def is_input_requested(self):
        """
        Indicates if the emulator needs an update for the inputs.
        """
        return self._input_requested

    def power(self):
        """
        Set the console in its initial state.
        """
        self._cartridge.power()
        # TODO: There's a bit of circular dependency here, we should look into
        # fixing it.
        # CPU -> MemoryBus -> PPU -> CPU
        self._ppu = PPU(self._set_frame_ready, self._cartridge)

        self._memory_bus = MemoryBus(self._cartridge, self._ppu, self._gamepad, self._zapper)
        self._cpu = CPU(self._ppu, self._memory_bus)
        self._apu = APU(self._memory_bus)
        self._memory_bus.set_cpu_and_apu(self._cpu, self._apu)

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
        self._input_requested = False
        self._cpu.emulate()
        nb_cycles = self._cpu.nb_cycles - cycles_before

        self._cycles_since_last_controller_poll += nb_cycles
        if self._cycles_since_last_controller_poll > 10000:
            self._input_requested = True
            self._cycles_since_last_controller_poll = 0

        for i in range(nb_cycles):
            self._ppu.emulate_once()
            self._ppu.emulate_once()
            self._ppu.emulate_once()

        self._apu.emulate(nb_cycles)

        self._zapper.update_light_state(self._ppu.pixels)

    def emulate(self):
        """
        Emulates until the emulator has rendered a complete frame or
        controller input should be refreshed.
        """
        self._frame_ready = False
        self._input_requested = False
        while not self._frame_ready:
            cycles_before = self._cpu.nb_cycles
            self._cpu.emulate()
            # The correct way to emulate PPU and APU cycles would be to emulate
            # them after each CPU tick. Unfortunately, this seems like an inefficient
            # way of doing things and the performance is much much slower.
            #
            # Instead, we'll count how many cycles have passed during the instruction
            # and then emulate the PPU accordingly. This isn't as precise
            # as the real hardware, but it's hopefully a good balance between
            # accuracy and speed for a Python based interpreter.
            nb_cycles = self._cpu.nb_cycles - cycles_before

            # Every 10,000 CPU cycles we'll update the controller states,
            # so that's roughly 190 times per second, which means we get about
            # 3 updates per frame, allowing sub frame input updates.
            self._cycles_since_last_controller_poll += nb_cycles
            if self._cycles_since_last_controller_poll > 10000:
                self._input_requested = True
                self._cycles_since_last_controller_poll = 0

            for i in range(nb_cycles):
                self._ppu.emulate_once()
                self._ppu.emulate_once()
                self._ppu.emulate_once()

            self._apu.emulate(nb_cycles)

            self._zapper.update_light_state(self._ppu.pixels)

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
    def apu(self):
        """
        Access the APU.
        """
        return self._apu

    @property
    def ppu(self):
        """
        Access the PPU.
        """
        return self._ppu

    @property
    def gamepad(self):
        """
        Access the gamepad connected to port 1.
        """
        return self._gamepad

    @property
    def zapper(self):
        """
        Access the Zapper connected to port 2.
        """
        return self._zapper
