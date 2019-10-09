# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

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

    # Maps key presses to Gamepad 1 buttons.
    _keys_to_gamepad = {
        sdl2.SDL_SCANCODE_X: "a",
        sdl2.SDL_SCANCODE_Z: "b",
        sdl2.SDL_SCANCODE_S: "start",
        sdl2.SDL_SCANCODE_A: "select",
        sdl2.SDL_SCANCODE_UP: "up",
        sdl2.SDL_SCANCODE_DOWN: "down",
        sdl2.SDL_SCANCODE_LEFT: "left",
        sdl2.SDL_SCANCODE_RIGHT: "right",
    }

    # Maps joystick button presses to Gamepad 1 buttons.
    _buttons_to_gamepad = {
        sdl2.SDL_CONTROLLER_BUTTON_X: "b",
        sdl2.SDL_CONTROLLER_BUTTON_Y: "b",
        sdl2.SDL_CONTROLLER_BUTTON_A: "a",
        sdl2.SDL_CONTROLLER_BUTTON_B: "a",
        sdl2.SDL_CONTROLLER_BUTTON_BACK: "select",
        sdl2.SDL_CONTROLLER_BUTTON_START: "start",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: "up",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: "down",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: "left",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: "right",
    }

    _save_state_keys = [
        sdl2.SDL_SCANCODE_1,
        sdl2.SDL_SCANCODE_2,
        sdl2.SDL_SCANCODE_3,
        sdl2.SDL_SCANCODE_4,
    ]

    def _prepare_window(self):
        """
        Shows the Window
        """
        sdl2.ext.init()
        sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER)

        # Width in the monitor's pixel of a single pixel from the emulator.
        self._window_multiplier = 4

        # Creates a RGB dialog.
        self._window = sdl2.ext.Window(
            "EmNES", size=(256 * self._window_multiplier, 240 * self._window_multiplier)
        )
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

        sdl2.SDL_RenderCopy(self._renderer, self._texture, None, None)
        sdl2.SDL_RenderPresent(self._renderer)

        # Run the event pump to know if we should quit the app.
        return self._event_pump()

    def _read_inputs(self):
        """
        Updates controller state.
        """
        # Controller state update is done inside the event pump.
        return self._event_pump()

    def _event_pump(self):
        """
        Retrieves pending event from the event loop and processes
        them to update the controller state.

        :returns: If True, the user has not dismissed the emulator window and
            the emulation should keep running.
        """
        keep_running = True

        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                keep_running = False
            # Keyboard handling
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.scancode in self._keys_to_gamepad:
                    setattr(
                        self._nes.gamepad, self._keys_to_gamepad[event.key.keysym.scancode], True
                    )
            elif event.type == sdl2.SDL_KEYUP:
                if event.key.keysym.scancode in self._keys_to_gamepad:
                    setattr(
                        self._nes.gamepad, self._keys_to_gamepad[event.key.keysym.scancode], False
                    )
                if event.key.keysym.scancode in self._save_state_keys:
                    slot_index = self._save_state_keys.index(event.key.keysym.scancode) + 1
                    if event.key.keysym.mod & sdl2.KMOD_SHIFT:
                        self._save_state(slot_index)
                    else:
                        self._load_state(slot_index)
            # Game controller handling.
            elif event.type == sdl2.SDL_CONTROLLERDEVICEADDED:
                # When controller is detected, add it!
                sdl2.SDL_GameControllerOpen(event.jdevice.which)
            elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                if event.cbutton.button in self._buttons_to_gamepad:
                    setattr(self._nes.gamepad, self._buttons_to_gamepad[event.cbutton.button], True)
            elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                if event.cbutton.button in self._buttons_to_gamepad:
                    setattr(
                        self._nes.gamepad, self._buttons_to_gamepad[event.cbutton.button], False
                    )
            # Mouse handling for zapper
            elif event.type == sdl2.SDL_MOUSEMOTION:
                x = event.button.x // self._window_multiplier
                y = event.button.y // self._window_multiplier
                self._nes.zapper.update_aim_location(x, y)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                if event.button.button == sdl2.SDL_BUTTON_LEFT:
                    self._nes.zapper.trigger_pulled = True
            elif event.type == sdl2.SDL_MOUSEBUTTONUP:
                if event.button.button == sdl2.SDL_BUTTON_LEFT:
                    self._nes.zapper.trigger_pulled = False

        return keep_running

    def _finalize_window(self):
        """
        Finalize SDL.
        """
        sdl2.ext.quit()


def main():
    Emulator().run()


if __name__ == "__main__":
    main()
