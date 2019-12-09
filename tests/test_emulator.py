# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

import os
import re
from collections import namedtuple
import hashlib

import pytest

from emnes import NES


def _get_output_from_0x6400(bus):
    i = 0
    while bus.read_byte(0x6004 + i) != 0:
        i += 1
    return bus.read_array(0x6004, i).decode("utf-8")


@pytest.mark.parametrize(
    "rom_location",
    [
        # Ensures instrutions all work properly
        "roms/cpu/instructions/blargg/official_only.nes",
        # Ensures registers are in the right state on power up
        # and reset.
        "roms/cpu/reset/registers.nes",
        # Ensures the RAM is in the right state after a reset.
        "roms/cpu/reset/ram_after_reset.nes",
    ],
)
def test_blargg(rom_location):
    """
    Runs a blargg test suite by monitoring memory to know if the test
    passed or failed.
    """
    test_rom = os.path.join(os.path.dirname(__file__), *rom_location.split("/"))
    nes = NES()
    nes.load_rom(test_rom)

    tests_are_running = False

    # The test roms initialize the emulator and when they are ready to start running
    # tests they will set 0x6001 to 0x6003 with DEB061. When this is set,
    # the tests are considered as running and we can start monitoring the value
    # at 0x6000 that indicates the status of the test.

    power_pressed = False
    # This is how many cycles the blargg test suite takes when ppu is emulated.
    while nes.cpu.nb_cycles < 55211018:

        nes.emulate_once()
        nes.apu.samples
        if tests_are_running is False:
            tests_are_running = nes.memory_bus.read_array(0x6001, 3) == b"\xDE\xB0\x61"
            continue

        # If the test has ended
        if nes.memory_bus.read_byte(0x6000) == 0x00:
            break
        elif nes.memory_bus.read_byte(0x6000) < 0x80:
            raise Exception(
                "Test failed. Here's the test output:\n\n" + _get_output_from_0x6400(nes.memory_bus)
            )
        elif nes.memory_bus.read_byte(0x6000) == 0x81 and not power_pressed:
            print("Pressing power.")
            # This code means the console needs to be reset about 100 ms from now.
            # 100 ms is 1/10th of a second, which is roughly 170,000 CPU cycles.
            wait_end = nes.cpu.nb_cycles + 170000
            while nes.cpu.nb_cycles < wait_end:
                nes.emulate_once()
                nes.apu.samples
            nes.reset()
            power_pressed = True
    else:
        # Test shouldn't have passed by now.
        assert nes.memory_bus.read_byte(0x6000) != 0x00
        raise Exception(
            "Test took too long to execute! Here's the test output:\n\n"
            + _get_output_from_0x6400(nes.memory_bus)
        )


@pytest.mark.parametrize(
    "rom_location,nb_cycles,ppu_md5",
    [
        ("roms/cpu/timing/cpu_timing_test.nes", 19652633, "d1a71ada4584b8048d77517ce8cc1f01"),
        ("roms/ppu/blargg_ppu_tests/vram_access.nes", 1784334, "0941a56e4c62c6026264952a9bfaea35"),
        ("roms/ppu/blargg_ppu_tests/palette_ram.nes", 1784334, "0941a56e4c62c6026264952a9bfaea35"),
        ("roms/ppu/blargg_ppu_tests/sprite_ram.nes", 1784334, "0941a56e4c62c6026264952a9bfaea35"),
    ],
)
def test_run_and_compare_output(rom_location, nb_cycles, ppu_md5):
    """
    Runs a blargg test suite for a specific number of cycles and compares
    the PPU output to ensure
    """
    test_rom = os.path.join(os.path.dirname(__file__), *rom_location.split("/"))
    nes = NES()
    nes.load_rom(test_rom)
    while nes.cpu.nb_cycles < nb_cycles:
        nes.emulate_once()
        nes.apu.samples
    assert nes.cpu.nb_cycles == nb_cycles
    assert hashlib.md5(nes.ppu.pixels).hexdigest() == ppu_md5


# D256  C9 01     CMP #$01                        A:01 X:33 Y:88 P:25 SP:FB PPU:308, 35 CYC:4088
line_re = re.compile(
    # Matches C000, then skips everything up to A: and
    # starts grabbing registers one by one.
    # To debug this regular expression, visit https://rubular.com/r/E9xI5IHaIHADIz
    r"(\w*).*A:(\w*) X:(\w*) Y:(\w*) P:(\w*) SP:(\w*) PPU:\s*(\w*),\s*(\w*) CYC:(\d*)"
)

ProcessorState = namedtuple(
    "ProcessorState",
    [
        "program_counter",
        "accumulator",
        "index_x",
        "index_y",
        "status",
        "stack_pointer",
        "ppu_x",
        "ppu_y",
        "nb_cycles",
    ],
)


def parse_neslog_line(line):
    """
    Parse a line from nestest.log

    :param str line: Line to parse.

    :returns: nameduple of (
        program_counter, accumulator, index_x, index_y, status, stack_point, nb_cycles
    )
    """
    return ProcessorState(
        *[
            int(value, 16) if idx < 6 else int(value)
            for idx, value in enumerate(line_re.match(line).groups())
        ]
    )


def test_neslog_parser():
    """
    Test the nestest.log parser.
    """
    line = "D256  C9 01     CMP #$01                        A:01 X:33 Y:88 P:25 SP:FB PPU:308, 35 CYC:4088"  # noqa
    result = parse_neslog_line(line)
    assert result.program_counter == 0xD256
    assert result.accumulator == 0x01
    assert result.index_x == 0x33
    assert result.index_y == 0x88
    assert result.status == 0x25
    assert result.stack_pointer == 0xFB
    assert result.ppu_x == 308
    assert result.ppu_y == 35
    assert result.nb_cycles == 4088


def test_nestest():
    """
    Ensures various instruction operations are valid and that the registers have the right value.

    It also tests a few unofficial opcodes, but not all.
    """
    test_log = os.path.dirname(__file__) + "/roms/cpu/instructions/nestest/nestest.log"
    test_rom = os.path.dirname(__file__) + "/roms/cpu/instructions/nestest/nestest.nes"
    nes = NES()
    nes.load_rom(test_rom)

    # The nestest.txt file inside the roms/cpu/nestest/nestsest.txt explains
    # how to setup our automated test.
    nes.cpu.program_counter = 0xC000
    nes.cpu.stack_pointer = 0xFD
    nes.cpu.nb_cycles = 7

    previous_cycle = 0
    previous_expected_cycle = 0
    previous_line = ""

    for line_idx, line in enumerate(open(test_log, "rt")):
        # Break on this line in the file, as we don't support opcodes
        # past this address.
        if line_idx == 5003:
            break
        try:
            state = parse_neslog_line(line)
            assert hex(state.program_counter) == hex(nes.cpu.program_counter)
            assert hex(state.accumulator) == hex(nes.cpu.accumulator)
            assert hex(state.index_x) == hex(nes.cpu.index_x)
            assert hex(state.index_y) == hex(nes.cpu.index_y)
            assert hex(state.stack_pointer) == hex(nes.cpu.stack_pointer)
            assert hex(state.status) == hex(nes.cpu.status)
            assert (state.ppu_x, state.ppu_y) == nes.ppu.current_pixel

            expected_cycle = state.nb_cycles
            current_cycle = nes.cpu.nb_cycles

            nb_cycles_for_instruction = current_cycle - previous_cycle
            nb_expected_cycles_for_instruction = expected_cycle - previous_expected_cycle
            assert nb_cycles_for_instruction == nb_expected_cycles_for_instruction

            previous_expected_cycle = expected_cycle
            previous_cycle = current_cycle
            previous_line = line
            nes.emulate_once()
        except Exception:
            print(f"Line index: {line_idx}")
            print(f"Failed on:")
            print(line)
            print(f"Previous:")
            print(f"{previous_line}")
            raise
