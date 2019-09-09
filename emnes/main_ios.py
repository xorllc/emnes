# -*- coding: utf-8 -*-
import sys
import os
import time

from PIL import Image
import canvas
import clipboard

sys.path.insert(0, "..")
from emnes.emulator_base import EmulatorBase  # noqa


class Emulator(EmulatorBase):
    """
    Emulator loop for iOS.
    """

    def _prepare_window(self):
        """
        Prepares the image buffer and render canvas.
        """
        canvas.set_size(256, 240)
        self._img_data = bytearray(256 * 240 * 4)
        self._image = Image.new("RGB", [256, 231], color=None)

    def _update_window(self):
        """
        Updates the canvas.
        """
        self._fill(self._img_data, self._nes.ppu.pixels)
        self._image.frombytes(bytes(self._img_data))
        clipboard.set_image(self._image)
        canvas.draw_clipboard(0, 0, 256, 240)

    def _finalize_window(self):
        """
        Nothing to do.
        """
        pass


if __name__ == "__main__":
    Emulator().run()
