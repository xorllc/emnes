#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

import sys
import os
import time
import argparse

repo_root = os.path.join(os.path.dirname(__file__), "..")

sys.path.insert(0, repo_root)

import emnes  # noqa

parser = argparse.ArgumentParser(description="NES emulator")
parser.add_argument("--nb-runs", "-n", type=int, default=1, help="number of times to run the rom")

args = parser.parse_args()


def print_cartridge_info(cart):
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


def get_output_from_0x6400(bus):
    """
    Reads the string at 0x6400.

    :param emnes.MemoryBus bus: Memory bus.

    :returns: String at 0x6400.
    """
    i = 0
    while bus.read_byte(0x6004 + i) != 0:
        i += 1
    return bus.read_array(0x6004, i).decode("utf-8")


def main():
    """
    Runs the blargg rom test.
    """
    nes = emnes.nes.NES()
    nes.load_rom(
        os.path.join(
            os.path.dirname(__file__),
            *"../tests/roms/cpu/instructions/blargg/official_only.nes".split("/"),
        )
    )
    print_cartridge_info(nes.cartridge)

    before = time.time()
    nb_instructions = 0
    nb_cycles = 0

    for i in range(args.nb_runs):
        # The Blarg test suites initializes memory 0x6001-0x6003 to let the test
        # running the emulator that the result at 0x6000 can be read to interpret
        # the result of the tests. So loop until we reach that milestone.
        while (
            nes._memory_bus.read_byte(0x6001) != 0xDE
            and nes._memory_bus.read_byte(0x6002) != 0xB0
            and nes._memory_bus.read_byte(0x6003) != 0x61
        ):
            nes._cpu.emulate()
            nb_instructions += 1

        # Now that we know that the tests are actually running, we can start monitoring
        # 0x6000. 0x00 means success, 0x01 - 0x7F means error, 0x80 and higher means running
        while nes._memory_bus.read_byte(0x6000) >= 0x80:
            nes._cpu.emulate()
            nb_instructions += 1

        if nes.memory_bus.read_byte(0x6000) != 0:
            print(get_output_from_0x6400(nes.memory_bus))
            return

        # Power cycling the emulator resets the cycle count so keep track of the number of cycles.
        nb_cycles += nes.cpu.nb_cycles

        # Do a full power cycle when the tests are done executing so we can reset the memory
        # content
        nes.power()

    elapsed = time.time() - before
    real_cpu_clock_rate = 1789773
    cycles_per_second = nb_cycles / elapsed
    print("===================================")
    print(f"Result: {nes._memory_bus.read_byte(0x6000)}")
    print(f"Instructions: {nb_instructions}")
    print(f"Cycles: {nb_cycles}")
    print(f"Cycles per second: {cycles_per_second}")
    print(f"Emulated to Real speed ratio: {cycles_per_second / real_cpu_clock_rate}")
    print(f"Elapsed: {elapsed} seconds")
    print(f"Average: {elapsed / args.nb_runs} seconds")


if __name__ == "__main__":
    main()
