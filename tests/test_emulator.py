# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

import os
import re
from collections import namedtuple
from emnes import NES


def _get_output_from_0x6400(bus):
    i = 0
    while bus.read_byte(0x6004 + i) != 0:
        i += 1
    return str(bus.read_array(0x6004, i))


def test_blargg():
    """
    Ensures all instructions do as espected.
    """
    test_rom = os.path.dirname(__file__) + "/roms/cpu/blargg/official_only.nes"
    nes = NES()
    nes.load_rom(test_rom)

    tests_are_running = False

    # The test roms initialize the emulator and when they are ready to start running
    # tests they will set 0x6001 to 0x6003 with DEB061. When this is set,
    # the tests are considered as running and we can start monitoring the value
    # at 0x6000 that indicates the status of the test.
    for i in range(17500000):
        if tests_are_running is False:
            tests_are_running = nes.memory_bus.read_array(0x6001, 3) == b"\xDE\xB0\x61"
        nes.emulate()
        # If the test has ended
        if tests_are_running and nes.memory_bus.read_byte(0x6000) == 0x00:
            break
        elif tests_are_running and nes.memory_bus.read_byte(0x6000) < 0x80:
            raise Exception(
                "Test failed. Here's the test output:\n\n" + _get_output_from_0x6400(nes.memory_bus)
            )
    else:
        raise Exception(
            "Test took too long to execute! Here's the test output:\n\n"
            + _get_output_from_0x6400(nes.memory_bus)
        )


# C000  4C F5 C5  JMP $C5F5                       A:00 X:00 Y:00 P:24 SP:FD PPU:  0,  0 CYC:7
line_re = re.compile(
    # Matches C000, then skips everything up to A: and
    # starts grabbing registers one by one.
    r"(\w*).*A:(\w*) X:(\w*) Y:(\w*) P:(\w*) SP:(\w*).*CYC:(-{0,1}\d*)"
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
    line = "D1EE  A9 55     LDA #$55                        A:11 X:23 Y:46 P:E5 SP:FB PPU:337, 34 CYC:-1"  # noqa
    result = parse_neslog_line(line)
    assert result.program_counter == 0xD1EE
    assert result.accumulator == 0x11
    assert result.index_x == 0x23
    assert result.index_y == 0x46
    assert result.status == 0xE5
    assert result.stack_pointer == 0xFB
    assert result.nb_cycles == -1


def test_nestest():
    """
    Ensures various instruction operations are valid and that the registers have the right value.

    It also tests a few unofficial opcodes, but not all.
    """
    test_log = os.path.dirname(__file__) + "/roms/cpu/nestest/nestest.log"
    test_rom = os.path.dirname(__file__) + "/roms/cpu/nestest/nestest.nes"
    nes = NES()
    nes.load_rom(test_rom)

    # The nestest.txt file inside the roms/cpu/nestest/nestsest.txt explains
    # how to setup our automated test.
    nes.cpu.program_counter = 0xC000
    nes.cpu.stack_pointer = 0xFD
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
            # assert hex(state.nb_cycles) == hex(nes.cpu.nb_cycles)
            nes.emulate()
        except Exception:
            print(f"Failed on line {line_idx + 1}.")
            raise
