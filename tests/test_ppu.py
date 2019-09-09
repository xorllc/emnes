# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

import pytest

from emnes.ppu import PPU

zero_ppu_ctrl = {
    "base_nametable_address": 0x2000,
    "vram_io_addr_inc": 1,
    "sprite_table_addr": 0,
    "bg_table_addr": 0,
    "sprite_height": 8,
    "is_output_color_ext_pins": False,
    "generate_nmi": False,
}
zero_ppu_mask = {
    "greyscale": False,
    "show_leftmost_bg": False,
    "show_leftmost_sprite": False,
    "show_bg": False,
    "show_sprite": False,
    "emphasize_red": False,
    "emphasize_green": False,
    "emphasize_blue": False,
}


@pytest.mark.parametrize(
    "name,addr,zero_state,tests",
    [
        (
            "ppuctrl",
            0x2000,
            zero_ppu_ctrl,
            [
                (0, {}),
                (0b1, {"base_nametable_address": 0x2400}),
                (0b10, {"base_nametable_address": 0x2800}),
                (0b11, {"base_nametable_address": 0x2C00}),
                (0b100, {"vram_io_addr_inc": 32}),
                (0b1000, {"sprite_table_addr": 0x1000}),
                (0b100000, {"sprite_height": 16}),
                (0b1000000, {"is_output_color_ext_pins": True}),
                (0b10000000, {"generate_nmi": True}),
            ],
        ),
        (
            "ppumask",
            0x2001,
            zero_ppu_mask,
            [
                (0, {}),
                (0b1, {"greyscale": True}),
                (0b10, {"show_leftmost_bg": True}),
                (0b100, {"show_leftmost_sprite": True}),
                (0b1000, {"show_bg": True}),
                (0b10000, {"show_sprite": True}),
                (0b100000, {"emphasize_red": True}),
                (0b1000000, {"emphasize_green": True}),
                (0b10000000, {"emphasize_blue": True}),
            ],
        ),
    ],
)
def test_ppu_writable_register(name, addr, zero_state, tests):
    """
    Tests assignment to a register.

    :param str name: Name of the register property on the PPU
    :param int addr: Adress of the register in the PPU
    :param dict zero_state: State of the fields when the register has zero in it.
    :param list tests: List of tuples where th first value to update the
        register with and the second is a dictionary with the update fields and
        their values.
    """
    ppu = PPU()
    for value, updated_fields in tests:
        # we write via the address to test assignment from the MemoryBus
        ppu.write_byte(addr, value)
        # we ensure the result via the register variable
        register = getattr(ppu, name)
        expected = {**zero_state, **updated_fields}
        for field, value in expected.items():
            assert getattr(register, field) == value


def test_ppu_addr_register():
    """
    Ensure the proper functioning of the PPUADDR register.
    """
    ppu = PPU()

    # Ensure the most significant byte is updated first.
    assert ppu.vram_address == 0x0000

    ppu.write_byte(0x2006, 0x12)
    # The VRAM address shouldn't have been updated yet.
    assert ppu.vram_address == 0x00

    ppu.write_byte(0x2006, 0x34)
    # The VRAM address should now have been updated.
    assert ppu.vram_address == 0x1234

    ppu.write_byte(0x2006, 0x00)
    # The VRAM address should not be updated yet.
    assert ppu.vram_address == 0x1234

    ppu.write_byte(0x2006, 0x15)
    # The VRAM should now be set
    assert ppu.vram_address == 0x0015


def test_ppu_status_register():
    """
    Ensure the proper functioning of the PPUSTATUS register.
    """
    ppu = PPU()
    register = ppu.ppustatus

    # Ensure the write latch gets cleared when PPUSTATUS is read.
    # This can be tested by writing to ppuaddr, which sets the latch
    # then clear it by reading ppustatus and then writing again to ppuaddr.
    ppu.ppuaddr.write(0x12)
    assert ppu.vram_address == 0
    ppu.read_byte(0x2002)
    assert ppu.vram_address == 0
    ppu.ppuaddr.write(0x12)
    assert ppu.vram_address == 0
    ppu.ppuaddr.write(0x34)
    assert ppu.vram_address == 0x1234

    # Tests the sprite overflow flag. It should not reset on it's own.
    register.sprite_overflow = True
    assert ppu.read_byte(0x2002) == 1 << 5
    assert ppu.read_byte(0x2002) == 1 << 5
    register.sprite_overflow = False
    assert ppu.read_byte(0x2002) == 0

    # Tests the sprite 0 hit. It should not reset on it's own.
    register.sprite_0_hit = True
    assert ppu.read_byte(0x2002) == 1 << 6
    assert ppu.read_byte(0x2002) == 1 << 6
    register.sprite_0_hit = False
    assert ppu.read_byte(0x2002) == 0

    register.in_vblank = True
    # Ensure vblank flag is set.
    assert ppu.read_byte(0x2002) == 1 << 7
    # Ensure vblank flag was reset after read.
    assert ppu.read_byte(0x2002) == 0


def test_ppu_data_register():
    """
    Ensure the proper functioning of the PPUSTATUS register.
    """
    ppu = PPU()
    ppu.ppuaddr.write(0)
    ppu.ppuaddr.write(0)
    ppu.ppudata.write(0xF3)
    assert ppu.read_ppu_byte(0) == 0xF3
    ppu.ppudata.write(0xAE)
    assert ppu.read_ppu_byte(1) == 0xAE
    ppu.ppuaddr.write(0x3F)
    ppu.ppuaddr.write(0xFF)
    ppu.ppudata.write(0x12)
    # Expect mirroring to kick in.
    assert ppu.read_ppu_byte(0x3F1F) == 0x12
    ppu.ppudata.write(0x34)
    assert ppu.read_ppu_byte(0) == 0x34


@pytest.fixture
def tile_data():
    """
    Tile data for the test.
    """
    # This sample tile data was taken from
    # http://wiki.nesdev.com/w/index.php/PPU_pattern_tables
    tile_data = bytearray(16)
    tile_data[0] = 0b01000001
    tile_data[1] = 0b11000010
    tile_data[2] = 0b01000100
    tile_data[3] = 0b01001000
    tile_data[4] = 0b00010000
    tile_data[5] = 0b00100000
    tile_data[6] = 0b01000000
    tile_data[7] = 0b10000000
    tile_data[8] = 0b00000001
    tile_data[9] = 0b00000010
    tile_data[10] = 0b00000100
    tile_data[11] = 0b00001000
    tile_data[12] = 0b00010110
    tile_data[13] = 0b00100001
    tile_data[14] = 0b01000010
    tile_data[15] = 0b10000111

    return tile_data


@pytest.fixture
def expected_tile_indexes():
    """
    Expected pixel indexes for the tile_data
    """
    # This sample tile data was taken from
    # http://wiki.nesdev.com/w/index.php/PPU_pattern_tables
    expected_str = (
        ".1.....3" "11....3." ".1...3.." ".1..3..." "...3.22." "..3....2" ".3....2." "3....222"
    )
    expected = bytearray([(0 if index == "." else int(index)) for index in expected_str])
    return expected


def _test_ppu_tile_render_with_2_level_cache(tile_data, expected_tile_indexes):
    """
    Check that pixel data gets merged properly from the two sections of a tile with a two level deep
    cache of 256 entry each.
    """
    tile_cache = []
    for first_byte in range(0, 256):
        tile_cache.append([])
        first_tile = tile_cache[first_byte]
        for second_byte in range(0, 256):
            computed_indexes = bytearray(8)
            pixel = 0
            for x in range(7, -1, -1):
                # Compute the mask used to extract the bit for the pixel.
                bit_tester = 1 << x
                # Add the bits. The first bit read is the lsb of a 2 bit value. The second bit at
                # y + 8 is the msb.
                index = ((bit_tester & first_byte) + ((bit_tester & second_byte) << 1)) >> x
                computed_indexes[pixel] = index
                pixel += 1
            first_tile.append(computed_indexes)

    import time

    before = time.time()
    # Two potential implementations, but if results are to be believed, the one with the indexes is
    # twice as fast.
    for repeat in range(260 * 240 * 60 // 64):
        computed_indexes = bytearray(64)
        for y in range(0, 8):
            computed_indexes[y * 8 : (y + 1) * 8] = tile_cache[tile_data[y]][tile_data[y + 8]]
    print(time.time() - before)
    assert computed_indexes == expected_tile_indexes


def _test_ppu_tile_render_with_1_level_cache(tile_data, expected_tile_indexes):
    """
    Check that pixel data gets merged properly from the two sections of a tile with a 64k bit
    pre-cached result table.
    """
    tile_cache = []
    for second_byte in range(0, 256):
        for first_byte in range(0, 256):
            computed_indexes = bytearray(8)
            pixel = 0
            for x in range(7, -1, -1):
                # Compute the mask used to extract the bit for the pixel.
                bit_tester = 1 << x
                # Add the bits. The first bit read is the lsb of a 2 bit value. The second bit at
                # y + 8 is the msb.
                index = ((bit_tester & first_byte) + ((bit_tester & second_byte) << 1)) >> x
                computed_indexes[pixel] = index
                pixel += 1
            tile_cache.append(computed_indexes)

    import time

    before = time.time()
    for repeat in range(260 * 240 * 60 // 64):
        computed_indexes = bytearray(64)
        for y in range(0, 8):
            computed_indexes[y * 8 : (y + 1) * 8] = tile_cache[
                tile_data[y] | (tile_data[y + 8] << 8)
            ]
    print(time.time() - before)
    assert computed_indexes == expected_tile_indexes


def _test_ppu_tile_render_without_cache(tile_data, expected_tile_indexes):
    """
    Check that pixel data gets merged properly from the two sections of a tile with bit manipulation
    during rendering.
    """
    import time

    before = time.time()
    for repeat in range(260 * 240 * 60 // 64):
        computed_indexes = bytearray(64)
        pixel = 0
        for y in range(0, 8):
            for x in range(7, -1, -1):
                # Compute the mask used to extract the bit for the pixel.
                bit_tester = 1 << x
                # Add the bits. The first bit read is the lsb of a 2 bit value. The second bit at
                # y + 8 is the msb.
                index = ((bit_tester & tile_data[y]) + ((bit_tester & tile_data[y + 8]) << 1)) >> x
                computed_indexes[pixel] = index
                pixel += 1
    print(time.time() - before)
    assert computed_indexes == expected_tile_indexes


def _test_latch_filling(ppu, tile_x_loaded, tile_y_loaded, expected_coarse_y, next_expected_tile_y):

    expected_coarse_x = tile_x_loaded % 32
    # No expected line change, so reused previous one.

    # We're expecting reads to happen on the fist nametable,
    expected_nametable_addr = (ppu.coarse_x % 32) + 0x2000 + 32 * ppu.coarse_y
    # The nametable has 32 tiles per row (0-31). If we go past the 32th tile,
    # then we should be reading from the next nametable horizontally. This is
    # 0x400 further.
    if tile_x_loaded > 31:
        expected_nametable_addr ^= 0x400
    if tile_y_loaded == 30:
        expected_nametable_addr ^= 0x800

    assert ppu._state == ppu.FETCH_NAMETABLE
    assert ppu.coarse_x == expected_coarse_x % 32
    assert ppu.coarse_y == expected_coarse_y
    assert ppu.current_nametable_addr == expected_nametable_addr
    ppu.emulate_once()
    assert ppu._state == ppu.STORE_NAMETABLE
    assert ppu.coarse_x == expected_coarse_x % 32
    assert ppu.coarse_y == expected_coarse_y
    assert ppu.current_nametable_addr == expected_nametable_addr
    ppu.emulate_once()
    assert ppu._state == ppu.FETCH_ATTRIBUTE
    assert ppu.coarse_x == expected_coarse_x % 32
    assert ppu.coarse_y == expected_coarse_y
    assert ppu.current_nametable_addr == expected_nametable_addr
    ppu.emulate_once()
    assert ppu._state == ppu.STORE_ATTRIBUTE
    assert ppu.coarse_x == expected_coarse_x % 32
    assert ppu.coarse_y == expected_coarse_y
    assert ppu.current_nametable_addr == expected_nametable_addr
    ppu.emulate_once()
    assert ppu._state == ppu.FETCH_PATTERN_LOW
    assert ppu.coarse_x == expected_coarse_x % 32
    assert ppu.coarse_y == expected_coarse_y
    assert ppu.current_nametable_addr == expected_nametable_addr
    ppu.emulate_once()
    assert ppu._state == ppu.STORE_PATTERN_LOW
    assert ppu.coarse_x == expected_coarse_x % 32
    assert ppu.coarse_y == expected_coarse_y
    assert ppu.current_nametable_addr == expected_nametable_addr
    ppu.emulate_once()
    assert ppu._state == ppu.FETCH_PATTERN_HIGH
    assert ppu.coarse_x == expected_coarse_x % 32
    assert ppu.coarse_y == expected_coarse_y
    assert ppu.current_nametable_addr == expected_nametable_addr
    ppu.emulate_once()
    assert ppu._state == ppu.STORE_PATTERN_HIGH
    assert ppu.coarse_x == expected_coarse_x % 32
    assert ppu.coarse_y == expected_coarse_y
    assert ppu.current_nametable_addr == expected_nametable_addr
    ppu.emulate_once()
    # Should have incremented by a single tile address.

    # When the last store brings us to cycle_x 257, the first cycle after last pixel cycle,
    # then the coarse_x and coarse_y values should have been incremented.
    if ppu._cycle_x == 257:
        # We should have wrapped back around to the original scroll X value, since we'll have
        # incremented 32 times by now.
        # FIXME: Pass in the actual SCROLL X value instead of harcoding 2
        assert ppu.coarse_x == 2
        # On line 7, 15, 23 (cycle y % 8 == 7), etc..., the coarse_y should be moved to the next
        # line.
        # FIXME: Pass in the actual scroll Y value instead of assuming 0 based.
        assert ppu.coarse_y == next_expected_tile_y
    else:
        # If we're on an intermediary increment, we should have grown
        # by 1. Note that we can wrap around at anytime.
        assert ppu.coarse_x == (expected_coarse_x + 1) % 32
        # The coarse y value should't be incremented before the last pixel
        # on this line.
        assert ppu.coarse_y == expected_coarse_y


def test_ppu_state():
    """
    Test the various states of the PPU.
    """
    ppu = PPU()

    ppu.ppumask.write(0xFF)

    odd_frame = False

    ppu._odd_frame = True
    ppu._cycle_x = 0
    ppu._cycle_y = 261
    ppu.ppuctrl.write(0)  # Disables NMI, 8 pixel high tiles, and 0x2000 nametable
    ppu.ppumask.show_bg = True
    ppu.ppuscroll.write(0)
    ppu.ppuscroll.write(0)
    ppu._state = ppu.PRE_RENDER_SCANLINE_START

    for i in range(340):
        ppu.emulate_once()

    for frame in range(4):
        # There are 240 scanlines to render.
        for line in range(240):
            assert ppu._fine_x == 0
            tile_y = line // 8
            next_line_tile_y = tile_y + int(ppu._cycle_y % 8 == 7)
            # We should always be between 0 and 29.
            next_expected_tile_y = (tile_y + int(ppu._cycle_y % 8 == 7)) % 30

            assert ppu.coarse_y == tile_y
            # We start at cycle 0
            assert ppu._state == ppu.CYCLE_0
            ppu.emulate_once()
            # Then we'll fetch 32 tiles over time, but the first tile being fetched it tile 2
            # (0-based)
            for tile_x in range(32):
                # print(
                #     f"Frame: {frame}, Line: {line}, Tile X: {tile_x}, Tile Y: {tile_y}"
                #     f"Coarse X: {ppu.coarse_x}, Coarse Y: {ppu.coarse_y}"
                # )
                _test_latch_filling(ppu, (tile_x + 2), tile_y, tile_y, next_expected_tile_y)

            for sprite_data in range(257, 321):
                assert ppu._state == ppu.LOAD_SPRITES
                ppu.emulate_once()

            # For these two fetches, we'll be fetching from the next line, which may
            # incure a line change.
            _test_latch_filling(
                ppu, 0, next_line_tile_y, next_expected_tile_y, next_expected_tile_y
            )
            _test_latch_filling(
                ppu, 1, next_line_tile_y, next_expected_tile_y, next_expected_tile_y
            )

            for wasted_nametable_fetches in range(4):
                assert ppu._state == ppu.WASTE_NAMETABLE_BYTE
                ppu.emulate_once()

        for wasted in range(341):
            assert ppu._state == ppu.POST_RENDER_SCANLINE
            ppu.emulate_once()

        for wasted in range(341):
            assert ppu._state == ppu.FIRST_VBLANK_SCANLINE
            ppu.emulate_once()

        for line in range(242, 261):
            for wasted in range(341):
                assert ppu._state == ppu.IDLE_VBLANK_SCANLINES
                ppu.emulate_once()

        for wasted in range(0, 280):
            assert ppu._state == ppu.PRE_RENDER_SCANLINE_START
            ppu.emulate_once()

        for loaded in range(280, 305):
            assert ppu._state == ppu.LOAD_VERTICAL_SCROLL
            ppu.emulate_once()

        for wasted in range(305, 321):
            assert ppu._state == ppu.WAIT_FOR_SCANLINE_TILE_FETCH
            ppu.emulate_once()

        # For these two fetches, we'll be fetching back from the first line.
        # TODO: We're hardcoding the first tiles to 0,0 and 1,0, but once we test
        # scroll, this will have to be computed.
        _test_latch_filling(ppu, 0, 0, next_expected_tile_y, next_expected_tile_y)
        _test_latch_filling(ppu, 1, 0, next_expected_tile_y, next_expected_tile_y)

        for i in range(0, 3 if odd_frame else 4):
            assert ppu._state == ppu.WASTE_NAMETABLE_BYTE
            ppu.emulate_once()

        odd_frame = not odd_frame
