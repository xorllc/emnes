# -*- coding: utf-8 -*-
"""EmNES emulator.

Usage:
    __main__.py <path-to-rom> [--no-vsync | --no-rendering] [--nb-seconds=<n>] [--no-jit-warmup] [--display-nametables]

Options:
    -h --help             Show this screen
    --no-rendering        Runs the emulator without rendering anything on the screen.
    --no-vsync            Disables VSync. Emulator runs as fast as possible.
    --display-nametables  Displays all nametables.
    --nb-seconds=<n>      Runs the emulation for n seconds (in emulator time) and quits.
                          This is useful for benchmarking.
    --no-jit-warmup       Disables JIT warmup (PyPy only). Faster game startup but poorer performance
                          up front.
"""

import os
import pickle
import sys
import time
import ctypes
import hashlib

from docopt import docopt

from emnes import NES


# This is the palette that is used by the NES. It was taken from:
# http://wiki.nesdev.com/w/index.php/PPU_palettes#2C02
pal = [
    (84, 84, 84),
    (0, 30, 116),
    (8, 16, 144),
    (48, 0, 136),
    (68, 0, 100),
    (92, 0, 48),
    (84, 4, 0),
    (60, 24, 0),
    (32, 42, 0),
    (8, 58, 0),
    (0, 64, 0),
    (0, 60, 0),
    (0, 50, 60),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (152, 150, 152),
    (8, 76, 196),
    (48, 50, 236),
    (92, 30, 228),
    (136, 20, 176),
    (160, 20, 100),
    (152, 34, 32),
    (120, 60, 0),
    (84, 90, 0),
    (40, 114, 0),
    (8, 124, 0),
    (0, 118, 40),
    (0, 102, 120),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (236, 238, 236),
    (76, 154, 236),
    (120, 124, 236),
    (176, 98, 236),
    (228, 84, 236),
    (236, 88, 180),
    (236, 106, 100),
    (212, 136, 32),
    (160, 170, 0),
    (116, 196, 0),
    (76, 208, 32),
    (56, 204, 108),
    (56, 180, 204),
    (60, 60, 60),
    (0, 0, 0),
    (0, 0, 0),
    (236, 238, 236),
    (168, 204, 236),
    (188, 188, 236),
    (212, 178, 236),
    (236, 174, 236),
    (236, 174, 212),
    (236, 180, 176),
    (228, 196, 144),
    (204, 210, 120),
    (180, 222, 120),
    (168, 226, 144),
    (152, 226, 180),
    (160, 214, 228),
    (160, 162, 160),
    (0, 0, 0),
    (0, 0, 0),
]


def fill(rgb_buffer, palette_buffer, width, height):
    """
    Convert palette buffer into RGB buffer.

    :param array rgb_buffer: Array of RGB values, one byte per component.
    :param bytearray palette_buffer: Array of pixels with one byte per pixel.
    """
    rgba_index = 0
    palette_index = 0
    for y in range(height):
        for x in range(width):
            color_index = palette_buffer[palette_index]
            color = pal[color_index]

            rgb_buffer[rgba_index] = color[0]
            rgb_buffer[rgba_index + 1] = color[1]
            rgb_buffer[rgba_index + 2] = color[2]
            rgba_index += 3
            palette_index += 1


class EmulatorBase:
    """
    Base class of the emulator.

    Takes care of the emulation loop, polling inputs and sending data for output.
    The derived classes are responsible for doing the actual I/O.

    The derived class must implement the following methods:

    - prepare_window, which should prepare the window the emulator will be
      running in
    - update_window, which should be used to redraw the window
    - finalize_window, which should be used to clean up the window
    """

    def _print_cartridge_info(self, cart):
        """
        Print cartridge information.

        :param emnes.Cartridge cart: Cartridge to display information from.
        """
        yes_no = {True: "Yes", False: "No"}
        print("Format: iNES")
        print(f"Nb ROM banks: {cart.nb_rom_banks}")
        print(f"Nb VROM banks: {cart.nb_vrom_banks}")
        print(f"Mirroring type: {cart.mirroring_type}")
        print(f"Battery Backed?: {yes_no[cart.is_battery_backed]}")
        print(f"Has Trainer?: {yes_no[cart.has_trainer]}")
        print(f"Mapper: {cart.__class__.__name__}")
        print(f"Nb SRAM banks: {cart.nb_sram_banks}")
        print(f"Expected ROM size: {cart.expected_rom_size}")

    def run(self):
        """
        Launches the emulation loop.
        """
        arguments = docopt(__doc__, version="EmNes 0.1.0")

        # Extract all the arguments.
        self._is_rendering = arguments["--no-rendering"] is False
        self._rom = arguments["<path-to-rom>"]
        self._jit_warmup = arguments["--no-jit-warmup"] == False
        self._nb_frames_to_render = (
            (int(arguments["--nb-seconds"]) * 60) if arguments["--nb-seconds"] else None
        )
        self._vsync_enabled = arguments["--no-vsync"]
        self._display_nametables = arguments["--display-nametables"] == False

        # Run the emulator.
        try:
            if self._is_rendering:
                self._prepare_window()
            self._main_loop()
        finally:
            if self._is_rendering:
                self._finalize_window()

    def _state_file(self, slot_index):
        """
        Computes the file location for the state file with the specified index.

        :param int slot_index: Index for which to compute the slot index.

        :returns: Path to the current rom's save state file for the given index.
        """
        return os.path.expanduser(f"~/.emnes/{self._nes.cartridge.name}.state_{slot_index}")

    def _save_state(self, slot_index):
        """
        Saves the emulator state to disk into the given slot.

        :param int slot_index: Index of the slot to save into.
        """
        path = self._state_file(slot_index)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(path, "wb") as f:
            pickle.dump(self._nes, f)

    def _load_state(self, slot_index):
        """
        Restores the emulator state from disk from the given slot.

        :param int slot_index: Index of the slot to load from.
        """
        # If there is no state to load for this slot, ignore the call.
        if not os.path.exists(self._state_file(slot_index)):
            return

        with open(self._state_file(slot_index), "rb") as f:
            self._nes = pickle.load(f)

    def _main_loop(self):
        """
        The main emulation loop.
        """
        self._nes = NES()
        self._nes.load_rom(self._rom)

        # The PyPy JIT takes a while to warm up and this means poor emulation performance for 2-3
        # seconds. To avoid this, run the rom for a bit so the JIT optimises the byte code
        # for a bit and power cycle the emulator to finally let it run.
        if "PyPy" in sys.version and self._jit_warmup:
            print("Optimising PyPy JIT")
            start = time.time()
            while time.time() - start < 5:
                self._nes.emulate()
            self._nes.power()

        self._print_cartridge_info(self._nes.cartridge)

        current_emulation_time = 0
        emulation_start = time.time()

        fps = 0
        frame_start_time = time.time()
        current_frame = 0
        while self._nb_frames_to_render is None or current_frame < self._nb_frames_to_render:
            self._nes.emulate()
            if self._nes.is_frame_ready():
                fps += 1
                current_frame += 1
                elapsed = time.time() - frame_start_time
                if elapsed > 1.0:
                    fps /= elapsed
                    print(f"FPS: {fps}")
                    fps = 0
                    frame_start_time = time.time()

                if self._is_rendering:
                    if self._update_window() is False:
                        break

            if self._nes.is_input_requested():
                if self._read_inputs() is False:
                    break

        emulation_length = time.time() - emulation_start
        if self._nb_frames_to_render is not None:
            print(
                f"Emulation lasted {emulation_length} seconds. Average of "
                f"{emulation_length / self._nb_frames_to_render / 60} seconds of "
                "emulation per CPU full cycle."
            )
        print("Emulator closed on cycle:", self._nes.cpu.nb_cycles)
        print("PPU output MD5:", hashlib.md5(self._nes.ppu.pixels).hexdigest())

    def _read_inputs(self):
        """
        Reads inputs and updates the controller state.
        """
        pass


if __name__ == "__main__":
    main()
