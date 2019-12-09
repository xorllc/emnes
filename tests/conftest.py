# -*- coding: utf-8 -*-
import sys
import os

import pytest

# Adds the emulator source code to the PYTHONPATH.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from emnes.apu.pulse import Pulse


@pytest.fixture
def pulse():
    pulse = Pulse(0x04000)
    pulse.enabled = True
    return pulse


@pytest.fixture
def clockable_pulse(pulse):
    pulse.write_byte(0x4003, 0)
    return pulse
