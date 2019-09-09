# -*- coding: utf-8 -*-
"""EmNES emulator.

Usage:
    __main__.py <path-to-rom> [--no-vsync | --no-rendering] [--nb-seconds=<n>] [--no-jit-warmup]

Options:
    -h --help           Show this screen
    --no-rendering      Runs the emulator without rendering anything on the screen.
    --no-vsync          Disables VSync. Emulator runs as fast as possible.
    --nb-seconds=<n>    Runs the emulation for n seconds (in emulator time) and quits.
                        This is useful for benchmarking.
    --no-jit-warmup     Disables JIT warmup (PyPy only). Faster game startup but poorer performance
                        up front.
"""

import sys
import time
import ctypes
import hashlib

import sdl2.ext
from docopt import docopt

from emnes import NES
from emnes.emulator_base import EmulatorBase


class Emulator(EmulatorBase):
    """
    SDL based emulator.
    """

    def _prepare_window(self):
        """
        Shows the Window
        """
        sdl2.ext.init()

        # Creates a RGB dialog.
        self._window = sdl2.ext.Window("EmNES", size=(512, 480))
        self._window.show()
        self._renderer = sdl2.SDL_CreateRenderer(
            self._window.window,
            -1,
            sdl2.SDL_RENDERER_ACCELERATED
            | (sdl2.SDL_RENDERER_PRESENTVSYNC if self._vsync_enabled is False else 0),
        )

        # Creates a surface to draw on in the dialog
        self._surface = sdl2.SDL_CreateRGBSurface(
            0, 256, 240, 32, 0, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000
        )

        # Creates a texture which we will apply on the surface/
        self._texture = sdl2.SDL_CreateTexture(
            self._renderer, sdl2.SDL_PIXELFORMAT_RGB24, sdl2.SDL_TEXTUREACCESS_STREAMING, 256, 240
        )

        # Array of RGB values that will be filled
        self._img_data = bytearray(256 * 240 * 3)

        # Cast into a ctypes compatible structure so we can pass the bytearray to SDL.
        self._ctypes_img_data = (ctypes.c_byte * (256 * 240 * 3)).from_buffer(self._img_data)

        # Fills the image black.
        self._fill(self._img_data, bytearray(256 * 240))
        try:
            sdl2.SDL_LockSurface(self._surface)
            ctypes.memmove(
                self._surface.contents.pixels,
                ctypes.addressof(self._ctypes_img_data),
                256 * 240 * 3,
            )

        finally:
            sdl2.SDL_UnlockSurface(self._surface)

        sdl2.SDL_UpdateTexture(self._texture, None, self._surface.contents.pixels, 256 * 3)

    def _update_window(self):
        """
        Draws the current frame and processes inputs.
        """
        keep_running = True
        pixels = ctypes.c_void_p()
        pitch = ctypes.c_int32(256 * 3)
        try:
            sdl2.SDL_LockTexture(self._texture, None, ctypes.byref(pixels), ctypes.byref(pitch))

            # ctypes is too slow on PyPy to directly update pixels, so fill an array
            # in Python and then memcpy it.
            # IDEA: Maybe we could use Cython here to copy the bytes directly into the
            # texture. This wouldn't give us much of a speed boost however. The entire
            # is_rendering block is at most about 0.02 second long. There are much
            # bigger problems to fix.
            self._fill(self._img_data, self._nes.ppu.pixels)
            sdl2.SDL_memcpy(pixels, ctypes.addressof(self._ctypes_img_data), 256 * 240 * 3)
        finally:
            sdl2.SDL_UnlockTexture(self._texture)

        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                keep_running = False

        sdl2.SDL_RenderCopy(self._renderer, self._texture, None, None)
        sdl2.SDL_RenderPresent(self._renderer)

        return keep_running

    def _finalize_window(self):
        """
        Finalize SDL.
        """
        sdl2.ext.quit()


if __name__ == "__main__":
    Emulator().run()
