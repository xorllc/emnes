# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class PPUCtrl:
    """
    Implements the PPUCTRL register.
    """

    BASE_NAMETABLE_ADDRESSES = {0: 0x2000, 1: 0x2400, 2: 0x2800, 3: 0x2C00}

    __slots__ = [
        "base_nametable_address",
        "vram_io_addr_inc",
        "sprite_table_addr",
        "bg_table_addr",
        "sprite_height",
        "is_output_color_ext_pins",
        "generate_nmi",
        "_ppu",
    ]

    def __init__(self, ppu):
        """
        Init.
        """
        self._ppu = ppu
        self.write(0)

    def write(self, value):
        """
        Updates control values from the register.

        :param int value: Byte to write.
        """
        # TODO: This isn't used anywhere right now, which is surely going to lead
        # to video glitches down the road. We'll look into it at that point.
        self.base_nametable_address = self.BASE_NAMETABLE_ADDRESSES[value & 0x3]
        self.vram_io_addr_inc = 32 if value & 0b100 else 1
        self.sprite_table_addr = 0x1000 if value & 0b1000 else 0x0000
        self.bg_table_addr = 0x1000 if value & 0b10000 else 0x0000
        self.sprite_height = 16 if value & 0b100000 else 8
        self.is_output_color_ext_pins = bool(value & 0b1000000)
        self.generate_nmi = bool(value & 0b10000000)

        # Insert the two least significant bits into bits 10-11.
        # See: http://wiki.nesdev.com/w/index.php/PPU_scrolling#Register_controls
        self._ppu._tmp_vram_address = (self._ppu._tmp_vram_address & 0b111001111111111) | (
            value & 0x3
        ) << 10

    def __format__(self, style):
        """
        Formats register information on a single line.

        :param str style: Ignored.

        :returns: A string.
        """
        return (
            f"base_nametable_address: {hex(self.base_nametable_address)} "
            f"vram_io_addr_inc: {self.vram_io_addr_inc} "
            f"bg_table_addr: {hex(self.bg_table_addr)}  "
            f"sprite_table_addr: {hex(self.sprite_table_addr)} "
            f"sprite_height: {self.sprite_height} "
            f"is_output_color_ext_pins: {self.is_output_color_ext_pins} "
            f"generate_nmi: {self.generate_nmi}"
        )

    def read(self):
        """
        Always return 0, PPUCTRL is a write-only register.
        """
        return 0


class PPUMask:
    """
    Implememts the PPUMask register flags.
    """

    __slots__ = [
        "greyscale",
        "show_leftmost_bg",
        "show_leftmost_sprite",
        "show_bg",
        "show_sprite",
        "emphasize_red",
        "emphasize_green",
        "emphasize_blue",
        "is_rendering_enabled",
    ]

    def __init__(self):
        """
        Init.
        """
        self.write(0)

    def __format__(self, style):
        """
        Formats register information on a single line.

        :param str style: Ignored.

        :returns: A string.
        """
        return (
            f"greyscale: {self.greyscale} "
            f"show_leftmost_bg: {self.show_leftmost_bg} "
            f"show_leftmost_sprite: {self.show_leftmost_sprite} "
            f"show_bg: {self.show_bg} "
            f"show_sprite: {self.show_sprite} "
            f"emphasize_red: {self.emphasize_red} "
            f"emphasize_green: {self.emphasize_green} "
            f"emphasize_blue: {self.emphasize_blue}"
        )

    def write(self, value):
        """
        Update the mask flags.

        :param int value: New register value
        """
        self.greyscale = bool(value & 0b1)
        self.show_leftmost_bg = bool(value & 0b10)
        self.show_leftmost_sprite = bool(value & 0b100)
        self.show_bg = bool(value & 0b1000)
        self.show_sprite = bool(value & 0b10000)
        self.emphasize_red = bool(value & 0b100000)
        self.emphasize_green = bool(value & 0b1000000)
        self.emphasize_blue = bool(value & 0b10000000)

        # This could have been a proprety, but it suck up a lot of CPU
        # times according to vmprof.
        self.is_rendering_enabled = self.show_sprite or self.show_bg

    def read(self):
        """
        Always return 0, PPUMASK is a write-only register.
        """
        return 0


class PPUStatus:
    """
    Impements PPUSTATUS Register.
    """

    __slots__ = ["sprite_overflow", "sprite_0_hit", "in_vblank", "_ppu"]

    def __init__(self, ppu):
        """
        Init.
        """
        self.sprite_overflow = False
        self.sprite_0_hit = False
        self.in_vblank = False
        self._ppu = ppu

    def read(self):
        """
        Reads the register.

        When read, the VBlank status bit is reset.

        :returns: The register value.
        """
        value = (
            (int(self.sprite_overflow) << 5)
            | (int(self.sprite_0_hit) << 6)
            | (int(self.in_vblank) << 7)
        )
        # This status gets reset after being read.
        self.in_vblank = False

        # This also resets the flag that selects if we're updating the high or
        # low byte of PPUADDR or the X or Y of PPUSCROLL.
        self._ppu._written_once = False
        return value

    def __format__(self, style):
        """
        Formats register information on a single line.

        :param str style: Ignored.

        :returns: A string.
        """
        return (
            f"sprite_overflow: {self.sprite_overflow} "
            f"sprite_0_hit: {self.sprite_0_hit} "
            f"in_vblank: {self.in_vblank}"
        )

    def write(self, value):
        """
        Never updates the register, as it is read only.
        """
        # This is a read-only register.


class PPUAddr:
    """
    Implements PPUAddr register.
    """

    __slots__ = ["_ppu"]

    def __init__(self, ppu):
        """
        Init.
        """
        self._ppu = ppu

    def read(self):
        """
        Always return 0, PPUADDR is a write-only register.
        """

    def write(self, value):
        """
        Write one byte to the register.

        The first write after a register reset through PPUStatus
        updates the high address byte. The second write updates
        the low address byte.
        """
        if self._ppu._written_once is False:
            self._ppu._tmp_vram_address = ((value & 0b00111111) << 8) | (
                self._ppu._tmp_vram_address & 0xFF
            )
        else:
            self._ppu._tmp_vram_address = (self._ppu._tmp_vram_address & 0xFF00) | value
            self._ppu._vram_address = self._ppu._tmp_vram_address

        self._ppu._written_once = not self._ppu._written_once

    def __format__(self, style):
        """
        Formats register information on a single line.

        :param str style: Ignored.

        :returns: A string.
        """
        return f"addr: {hex(self._ppu._vram_address)} " f"_written_once: {self._ppu._written_once}"


class PPUData:
    """
    Implements PPUDATA register.
    """

    __slots__ = ["_ppu", "_buffer"]

    def __init__(self, ppu):
        """
        Init.
        """
        self._ppu = ppu
        # Reads from the PPUData register are buffered. What this means is that when
        # you write PPUAddr and then load data from PPUData, you'll get the byte from
        # the last memory location, not the new one. This effectively means that
        # you get the result from the previous PPUADDR address.
        self._buffer = 0

    def read(self):
        """
        Read a byte from the PPU.
        """
        addr = self._ppu._vram_address & 0b11111111111111

        if addr < 0x2000:
            return_value = self._buffer
            self._buffer = self._ppu._pattern_table_memory[addr]
        # Then 0x2000-0x2FFF is nametable memory.
        # 0x3000-0x3EFF is just a mirror of 0x2000-0x2EFF
        elif addr < 0x3EFF:
            return_value = self._buffer
            # TODO: We probably need to implement mirroring here!!!
            self._buffer = self._ppu._memory[addr & 0x2FFF]
        elif addr == 0x3F10:
            return_value = self._ppu._memory[0x3F00]
            self._buffer = self._ppu._memory[addr & 0x2FFF]
        elif addr == 0x3F14:
            return_value = self._ppu._memory[0x3F04]
            self._buffer = self._ppu._memory[addr & 0x2FFF]
        elif addr == 0x3F18:
            return_value = self._ppu._memory[0x3F08]
            self._buffer = self._ppu._memory[addr & 0x2FFF]
        elif addr == 0x3F1C:
            return_value = self._ppu._memory[0x3F0C]
            self._buffer = self._ppu._memory[addr & 0x2FFF]
        # Then 0x3F00-0x3F1F is the palette memory
        # 0x3F20-0x3FFF is just a mirror of 0x3F00-0x3F1F
        else:
            # When reading the palette, you get the right byte right
            # away, but the buffer is filled with the value of the name table
            # entry "underneath" the palette address.
            return_value = self._ppu._memory[addr & 0x3F1F]
            self._buffer = self._ppu._memory[addr & 0x2FFF]

        self._ppu._vram_address += self._ppu._ppuctrl.vram_io_addr_inc

        return return_value

    def write(self, value):
        """
        Write a byte to the PPU.

        :param int value: Value to write to the PPU.
        """
        addr = self._ppu._vram_address & 0b11111111111111

        # Lower than 0x2000 is the pattern table memory.
        if addr < 0x2000:
            self._ppu._pattern_table_memory[addr] = value
        # Then 0x2000-0x2FFF is nametable memory.
        # 0x3000-0x3EFF is just a mirror of 0x2000-0x2EFF
        elif addr < 0x3EFF:
            # TODO: We probably need to implement mirroring here!!!
            self._ppu._memory[addr & 0x2FFF] = value
        # 3F10 is a mirror of 3F00
        elif addr == 0x3F10:
            self._ppu._memory[0x3F00] = value
        elif addr == 0x3F14:
            self._ppu._memory[0x3F04] = value
        elif addr == 0x3F18:
            self._ppu._memory[0x3F08] = value
        elif addr == 0x3F1C:
            self._ppu._memory[0x3F0C] = value
        # Then 0x3F00-0x3F1F is the palette memory
        # 0x3F20-0x3FFF is just a mirror of 0x3F00-0x3F1F
        else:
            self._ppu._memory[addr & 0x3F1F] = value

        self._ppu._vram_address += self._ppu._ppuctrl.vram_io_addr_inc


class PPUOamAddr:
    """
    Implements PPUOAMADDR register.
    """

    __slots__ = "_ppu", "addr"

    def __init__(self):
        """
        Init.
        """
        self.addr = 0

    def read(self):
        """
        Always return 0, PPUOAMADDR is a write-only register.
        """
        return 0

    def write(self, value):
        """
        Select the byte that will be read or written to in the OAM memory.
        """
        self.addr = value


class PPUOamData:
    """
    Implements PPUOMADATA register.
    """

    __slots__ = ["_ppu"]

    def __init__(self, ppu):
        """
        Init.
        """
        self._ppu = ppu

    def write(self, value):
        """
        Write a single byte to the OAM memory and increments the OAM ADDR by one.

        :param int value: Value to write.
        """
        self._ppu._oam_memory[self._ppu._ppuoamaddr.addr] = value
        self._ppu._ppuoamaddr.addr += 1

    def read(self):
        """
        Read a single byte from OAM memory, but does not increment OAM ADDR.

        :returns: The byte read.
        """
        # TODO: Implement dirty reads when cycle_x is <= 64
        # https://wiki.nesdev.com/w/index.php/PPU_sprite_evaluation
        return self._ppu._oam_memory[self._ppu._ppuoamaddr.addr & 64]


class PPUScroll:
    """
    Implements the PPUScroll register.
    """

    __slots__ = ["_ppu", "x", "y"]

    def __init__(self, ppu):
        """
        Init.
        """
        self._ppu = ppu

    def read(self):
        """
        Always return 0, PPUSCROLL is a write-only register.
        """
        return 0

    def write(self, value):
        """
        Write a component into the scroll register.

        First write writes the X scroll, second is the Y.

        :param int value: Value of the coordinate.
        """
        if not self._ppu._written_once:
            self._ppu._tmp_vram_address &= 0b111111111100000
            self._ppu._tmp_vram_address |= value >> 3
            self._ppu._fine_x = 0b111 & value
        else:
            self._ppu._tmp_vram_address &= 0b000110000011111
            self._ppu._tmp_vram_address |= (value & 0b111) << 12
            self._ppu._tmp_vram_address |= (value & 0b11111000) << 2

        self._ppu._written_once = not self._ppu._written_once

    def __format__(self, style):
        """
        Formats register information on a single line.

        :param str style: Ignored.

        :returns: A string.
        """
        return f"x: {self.x} " f"y: {self.y}"


class PPU:
    """
    Picture Processing Unit, used to draw of the screen.

    Memory
    ------
    The memory of the PPU is separated into three regions in the emulator: pattern table,
    nametable and palette and OAM memory.

    - The pattern table stores the the pixel data of each 8x8 or 8x16 tile patterns.
    - The nametable contains indices into the pattern table. This is what composes
      the images.
    - The palette contains 2 sets, one for sprites and one for the background) of
      4 palettes, which have 4 color each.
    - OAM memory contains the data for all the sprites in the current frame.

    OAM Memory
    ----------
    The OAM memory contains 64 sprites and each sprite takes 4 byte of memory. They are:
    - Y coordinate of a sprite
    - Pattern table index where pixel data is stored for this sprite.
    - Attribute (background/foreground priority, palette index, X/Y flip)
    - X coordinate of the sprite.

    States
    ------
    The PPU is organized as a state machine. The state is represented by a number
    and a given number will invoke the right method on the class.

    Each tick of the PPU, which happens 3 times per CPU cycle, sees two counters being
    evaluated and drive the state: the X cycle, which goes from 0 to 341 and Y cycle,
    or scanline, which goes from 0 to 261.

    Here are the different phases

    Scanline 0-239: The rendering phase
    ===================================

    Cycle 0 is an idle cycle.

    In this phase, X cycles 1-256 render each one pixel on the screen, for an
    image 256 pixels wide. This happens independently of the steps taken by the
    PPU below.

    Cycles 1-256 can be divided in 8 sub phases of one cycle each. Those sub
    phases are:
        - Two cycles for fetching/store an upcoming tile index in the name table.
        - Two cycles for fetching/store an attribute byte for that file.
        - Two cycles for fetching/store the first byte of the pixel data of the tile.
        - Two cycles for fetching/store the second byte of the pixel data of the tile.

    This process repeats 32 times. In other words, it lasts 256 cycles (32 * 8).
    The first tile that is retrieved is actually tile 2 (when counting from 0).
    More on why later.

    Cycles 257-320 are meant for loading the sprite data for the next scanline.

    Cycles 321-336 are meant to load tile 0 and 1 for the next scanline so that
    Cycle 1 can start rendering the pixels right away.

    Cycles 336-340 are spent fetching two name table bytes. It is unknown why.

    Scanline 240-259: Post rendering phase
    ======================================
    During this phase, the PPU does not attempt to read the PPU memory, so
    this is where the game can update the tile information safely.

    Scanline 240 is a dummy scan line where nothing happens.

    On the cycle 1 of scanline 241, the vBlank flag in the PPUStatus register
    is set. When this happens, a flag is raised in the processor to indicate
    that the current instruction should finish and then the program counter
    should jump to the VBlank interrupt handler store at 0xFFFA-0xFFFB in the
    CPU memory.

    The PPU keeps idling until cycle 1 on scanline 260, at which time it lowers the
    vblank status of the PPUStatus register.

    Finally, just like on scanlines 0-239, the CPU fetches the tile data for tiles
    0 and 1 on the next scanline, scanline 0, during cycles 321-336 and the spends
    4 cycles (3 on an odd frame) reading name table bytes.

    Rendering
    ---------
    As stated above, the PPU renders one pixel per cycle when executing cycles 1-256
    of the first 240 scanlines. For each pixel, the following happens:

    1. Load the pixel's color index information from the current tile.
    2. Find the first non-opaque pixel from a sprite that covers the tile's pixel.
    3. If both pixels are opaque and the first is the first from OAM memory, a special
       flag named Sprite-0 Hit is raised in PPUSTATUS
    4. An attribute bit in the sprite will indicate is the sprite from the pixel has
       priority over the background or not.
    5. The color of the winning pixel is used to load the correct value from the palette
       and the video buffer is updated with that value.
    """

    __slots__ = [
        ########################################################################
        # Array of external registers the CPU can access and...
        "_registers",
        # ... then the memory registers themselves.
        "_ppuctrl",
        "_ppumask",
        "_ppustatus",
        "_ppuaddr",
        "_ppudata",
        "_ppuoamaddr",
        "_ppuoamdata",
        "_ppuscroll",
        ########################################################################
        # List of internal registers.
        # Temporary VRAM Address
        "_tmp_vram_address",
        # VRAM address
        "_vram_address",
        # Horizontal offset into the frame.
        "_fine_x",
        # If the V register has been written to once.
        "_written_once",
        ########################################################################
        # Tracks PPU state: current stage, the current x/y cycles and if we're
        # on an odd-frame or not.
        "_cycle_x",
        "_cycle_y",
        "_odd_frame",
        "_state",
        ########################################################################
        # References back to other parts of the hardware.
        "_cpu",  # Used to notify of VBlank.
        "_memory_bus",  # Used to access memory.
        ########################################################################
        # Actual different memory regions of the PPU.
        # This represents memory 0x0000-0x1FFF
        "_pattern_table_memory",
        # This represents memory 0x2000-0x3FFF
        "_memory",
        # This is the sprite memory.
        "_oam_memory",
        ########################################################################
        # Shift registers used for tile rendering. When rendering we're constantly
        # loading byes from different memory regions and storing them inside
        # internal registers.
        #
        # We're keeping the whole line even though we only need the current tile
        # and the next two, which makes the implementation a lot easier.
        "_name_table_byte",
        "_pattern_high_bytes",
        "_pattern_low_bytes",
        "_attribute_bytes",
        ########################################################################
        # Counts which tile is being rendered and which is being fetched.
        "_current_tile_fetched",
        "_current_tile_rendered",
        ########################################################################
        # Array of rendered pixels and
        "_pixels",
        ########################################################################
        # When sprite data for the next line is fetched, this holds information
        # about which sprite will be in each pixel.
        "_sprite_priority",
        ########################################################################
        # Mask applied to nametable accesses.
        "_nametable_mirroring_mask",
        ########################################################################
        # Callback invoked when a new frame is ready.
        "_frame_ready_cb",
    ]

    # IDEA: Maybe we should turn most data from this class into a bytearray so we have something
    # we could pass down to a cython-based rendering loop.
    class Sprite:
        """
        Data about a sprite.
        """

        __slots__ = (
            ####################################################################
            # Left coordinate of the sprite.
            "left",
            ########################################################################
            # Attributes of the sprite.
            # Bit 7: Vertical mirroring
            # Bit 6: Horizontal mirroring
            # Bit 5: Foreground (0) or background (1) sprite.
            # Bit 0-1: Palette index
            "attributes",
            ########################################################################
            # High byte and low bytes of the pattern data.
            "pattern_high",
            "pattern_low",
            ########################################################################
            # Indicates if this is sprite zero, aka the first sprite in OAMDATA.
            # When set, a sprite's opaque pixel overlapping a background opaque pixel
            # will raise the sprite zero hit flag in PPUSTATUS.
            "is_sprite_zero",
        )

        def get_index(self, rendered_x):
            """
            Computes the color index in a palette.

            :param int rendered_x: X coordinate of the pixel being rendered.
            """
            pixel_index = rendered_x - self.left
            if self.attributes & 0b1000000:
                selected_pixel_index = pixel_index
            else:
                selected_pixel_index = 7 - pixel_index
            bit_tester = 1 << selected_pixel_index
            return (
                (bit_tester & self.pattern_low) | ((bit_tester & self.pattern_high) << 1)
            ) >> selected_pixel_index

    def __init__(self, frame_ready_cb=None):
        """
        Init
        """
        self._frame_ready_cb = frame_ready_cb or (lambda: None)
        self._cycle_x = 0
        self._cycle_y = 0
        self._written_once = False
        self._sprite_priority = [None] * 256

        # TODO: Splits this into _nametables and _palette
        self._memory = bytearray(0x4000)
        self._pattern_table_memory = bytearray(0x2000)
        self._oam_memory = bytearray(256)

        self._nametable_mirroring_mask = 0xFFFF

        self._current_tile_fetched = 0
        self._current_tile_rendered = 0
        self._name_table_byte = 0
        self._pattern_high_bytes = bytearray(34)
        self._pattern_low_bytes = bytearray(34)
        self._attribute_bytes = bytearray(34)
        self._fine_x = 0
        self._pixels = bytearray(256 * 240)

        self._tmp_vram_address = 0
        self._vram_address = 0

        self._odd_frame = False

        self._state = self.CYCLE_0

        self._ppuctrl = PPUCtrl(self)
        self._ppumask = PPUMask()
        self._ppuaddr = PPUAddr(self)
        self._ppudata = PPUData(self)
        self._ppuoamaddr = PPUOamAddr()
        self._ppuoamdata = PPUOamData(self)
        self._ppuscroll = PPUScroll(self)
        self._ppustatus = PPUStatus(self)

        self._registers = [
            self._ppuctrl,
            self._ppumask,
            self._ppustatus,
            self._ppuoamaddr,
            self._ppuoamdata,
            self._ppuscroll,
            self._ppuaddr,
            self._ppudata,
        ]

    @property
    def pixels(self):
        """
        Access the rendered pixels.
        """
        return self._pixels

    @property
    def ppuctrl(self):
        """
        Access PPUCTRL
        """
        return self._ppuctrl

    @property
    def ppumask(self):
        """
        Access PPUMASK
        """
        return self._ppumask

    @property
    def ppustatus(self):
        """
        Access PPUSTATUS
        """
        return self._ppustatus

    @property
    def ppuaddr(self):
        """
        Access PPUADDR
        """
        return self._ppuaddr

    @property
    def ppudata(self):
        """
        Access PPUDATA
        """
        return self._ppudata

    @property
    def ppuscroll(self):
        """
        Access PPUSCROLL
        """
        return self._ppuscroll

    @property
    def current_pixel(self):
        """
        The current pixel being draw by the PPU.
        """
        return (self._cycle_x, self._cycle_y)

    @property
    def coarse_x(self):
        """
        The current tile's X coordinate to fetch.
        """
        # Bits 0-4 are the coarse X
        return self._vram_address & 0b11111

    @property
    def coarse_y(self):
        """
        The current tile's Y coordinate to fetch.
        """
        # Bits 5-9 are the coarse Y
        return (self._vram_address & 0b1111100000) >> 5

    @property
    def fine_y(self):
        """
        The Y offset in the current frame.
        """
        # Bits 12-14 are the fine y scroll
        return (self._vram_address & 0b111000000000000) >> 12

    @property
    def vram_address(self):
        """
        Current VRAM address.
        """
        return self._vram_address & 0b11111111111111

    @property
    def current_nametable_addr(self):
        """
        The current nametable address, based on the vram address
        and the mirroring mask. This address gets updated after each high
        pattern byte has been fetched.
        """
        # Credit for this next line goes to
        # https://wiki.nesdev.com/w/index.php/PPU_scrolling#Tile_and_attribute_fetching
        return 0x2000 | (self._vram_address & 0x0FFF) & self._nametable_mirroring_mask

    def _set_cpu(self, cpu):
        """
        Assigns the CPU.
        """
        self._cpu = cpu

    def _set_memory_bus(self, memory_bus):
        """
        Assigns the memory bus.
        """
        self._memory_bus = memory_bus

    cpu = property(None, _set_cpu)
    memory_bus = property(None, _set_memory_bus)

    def read_byte(self, addr):
        """
        Read from PPU register.

        :param int addr: Address of the register to read.

        :returns: The byte read.
        """
        return self._registers[addr & 0x7].read()

    def write_byte(self, addr, value):
        """
        Write to a PPU register.

        :param int addr: Address of the register to write.
        :param int value: New value of the register.
        """
        self._registers[addr & 0x7].write(value)

    def set_mirroring_options(self, mask):
        """
        Set the mirroring to use when accessing the nametable data.
        """
        self._nametable_mirroring_mask = mask

    def configure(self, pattern_table_memory=None):
        """
        Configure various aspect of the PPU.

        :param bytes: Memory for the pattern table.
        """
        self._pattern_table_memory = pattern_table_memory

    def read_ppu_byte(self, addr):
        """
        Returns a byte from the PPU at the given address.

        :param int addr: Address to read a byte from.

        :returns: The byte read.
        """
        if addr < 0x2000:
            return self._pattern_table_memory[addr]
        else:
            return self._memory[addr]

    def emulate_once(self):
        """
        Emulates of PPU tick.
        """
        # This is actually noticably faster than indexing into an array
        # The states that occur the most often are tried out first.
        if self._state == self.LOAD_SPRITES:
            self._load_sprites()
        elif self._state == self.FETCH_NAMETABLE:
            self._fetch_nametable()
        elif self._state == self.STORE_NAMETABLE:
            self._store_nametable()
        elif self._state == self.FETCH_ATTRIBUTE:
            self._fetch_attribute()
        elif self._state == self.STORE_ATTRIBUTE:
            self._store_attribute()
        elif self._state == self.FETCH_PATTERN_LOW:
            self._fetch_pattern_low()
        elif self._state == self.STORE_PATTERN_LOW:
            self._store_pattern_low()
        elif self._state == self.FETCH_PATTERN_HIGH:
            self._fetch_pattern_high()
        elif self._state == self.STORE_PATTERN_HIGH:
            self._store_pattern_high()
        elif self._state == self.IDLE_VBLANK_SCANLINES:
            self._idle_vblank_scanlines()
        elif self._state == self.WASTE_NAMETABLE_BYTE:
            self._waste_nametable_byte()
        elif self._state == self.POST_RENDER_SCANLINE:
            self._post_render_scanline()
        elif self._state == self.FIRST_VBLANK_SCANLINE:
            self._first_vblank_scanline()
        elif self._state == self.PRE_RENDER_SCANLINE_START:
            self._pre_render_scanline_start()
        elif self._state == self.CYCLE_0:
            self._cycle_0()
        elif self._state == self.LOAD_VERTICAL_SCROLL:
            self._load_vertical_scroll()
        elif self._state == self.WAIT_FOR_SCANLINE_TILE_FETCH:
            self._wait_for_scanline_tile_fetch()
        else:
            raise RuntimeError(f"Unknown state {self._state}")

    # PPU states for the state machine.
    (
        CYCLE_0,
        FETCH_NAMETABLE,
        STORE_NAMETABLE,
        FETCH_ATTRIBUTE,
        STORE_ATTRIBUTE,
        FETCH_PATTERN_LOW,
        STORE_PATTERN_LOW,
        FETCH_PATTERN_HIGH,
        STORE_PATTERN_HIGH,
        WASTE_NAMETABLE_BYTE,
        POST_RENDER_SCANLINE,
        LOAD_SPRITES,
        FIRST_VBLANK_SCANLINE,
        IDLE_VBLANK_SCANLINES,
        PRE_RENDER_SCANLINE_START,
        LOAD_VERTICAL_SCROLL,
        WAIT_FOR_SCANLINE_TILE_FETCH,
    ) = range(17)

    def _render_pixel(self):
        """
        Renders the current pixel drawn by the CPU.

        It combines tile information with sprite information to produce
        a single pixel.
        """
        # Find how deep into the current tile we are.
        selected_pixel_index = 7 - ((self._cycle_x - 1 + self._fine_x) % 8)

        # IDEA: Only do sprite-0 hit here and postpone the rest of the rendering to the end of the
        # scanline in hope PyPy will optimize the tight loop of redundant code.

        # If rendering is disabled, there's no point evaluating any of this,
        # we'll only pick the background color.
        if self._ppumask.is_rendering_enabled:
            # Extract the current tile's pattern data
            bg_pattern_low = self._pattern_low_bytes[self._current_tile_rendered]
            bg_pattern_high = self._pattern_high_bytes[self._current_tile_rendered]

            # Compute the index of the bit and it's value for the given pixel.
            # Pixel 0 is 128, pixel 1 is 64 and so on.
            bit_tester = 1 << selected_pixel_index
            # Add the bits. The first bit in bg_pattern_low is the lsb of a 2 bit value.
            # The second bit in bg_pattern_high the msb.
            bg_color_index = (
                (bit_tester & bg_pattern_low) | ((bit_tester & bg_pattern_high) << 1)
            ) >> selected_pixel_index

            # Find the color of the pixel to render.
            sprite = self._sprite_priority[self._cycle_x - 1]
            sprite_color_index = sprite.get_index(self._cycle_x - 1) if sprite else 0

            # If sprite and bg are opaque and we're rendering sprite 0, raise the flag!
            if sprite_color_index != 0 and sprite.is_sprite_zero and bg_color_index != 0:
                self._ppustatus.sprite_0_hit = True

            # If the sprite's pixel is set and it should appear on top, then this is
            # the pixel to draw.
            if sprite_color_index and (sprite.attributes & 0b100000 == 0):
                palette_addr = 0x3F10 | ((sprite.attributes & 0b11) << 2) | sprite_color_index
            # The sprite pixel is not on top, so pick the background color if it is set.
            elif bg_color_index:
                palette_addr = (
                    0x3F00
                    | (self._attribute_bytes[self._current_tile_rendered] << 2)
                    | bg_color_index
                )
            # There was no background pixel, so pick the sprite pixel underneath it.
            elif sprite_color_index:
                palette_addr = 0x3F10 | ((sprite.attributes & 0b11) << 2) | sprite_color_index
            # No pixel found at all, so put the back color.
            else:
                palette_addr = 0x3F00
        else:
            palette_addr = 0x3F00

        # Store the palette index
        self._pixels[self._cycle_y * 256 | (self._cycle_x - 1)] = self._memory[palette_addr]

        # When the next pixel will be reached next, change the current tile rendered.
        if selected_pixel_index == 0:
            self._current_tile_rendered += 1

    def _get_pattern_addr(self, is_upper):
        """
        Calculate the address of a background tile in the pattern table based
        on the current name table byte.

        :param bool is_upper: If True, the upper byte if be retrieved.

        :returns: The address of the pattern byte.
        """
        return (
            self._ppuctrl.bg_table_addr
            | self.fine_y
            | ((self._name_table_byte) << 4)
            | (0b1000 if is_upper else 0)
        )

    def _update_x_scroll_bits(self):
        """
        Copy the X scroll bits from the temporary VRAM address to the VRAM address.
        """
        self._vram_address = (self._vram_address & 0b111101111100000) | (
            self._tmp_vram_address & 0b10000011111
        )

    ############################################################################
    # State machine
    #
    # The PPU state machine is pretty straight forward. The X cycle will help
    # with the transitions on a given scanline. The methods are generally split into
    # three sections:
    #
    # - render a pixel if the cycle can do it
    # - do some operation
    # - increment the X cycle and figure if there's a change in transition.
    #
    # The following methods represent the state machine.

    def _cycle_0(self):
        """
        Cycle 0.

        Initialized the PPU for rendering tiles.
        """
        self._cycle_x += 1
        self._current_tile_rendered = 0
        self._state = self.FETCH_NAMETABLE

    def _fetch_nametable(self):
        """
        Fetch nametable byte.

        This state, just like other fetch/store states, can be used both to
        read tiles 2 through 33 of the current line and to fetch tiles 0 and 1
        for the next line.
        """
        # Render the pixel
        if self._cycle_x <= 256:
            self._render_pixel()

        self._cycle_x += 1
        self._state = self.STORE_NAMETABLE

    def _store_nametable(self):
        """
        Store a nametable byte.
        """
        # Read the byte from memory.
        self._name_table_byte = self._memory[self.current_nametable_addr]

        # Render the pixel
        if self._cycle_x <= 256:
            self._render_pixel()

        # Update the state
        self._cycle_x += 1
        self._state = self.FETCH_ATTRIBUTE

    def _fetch_attribute(self):
        """
        Fetch the attribute for this tile.
        """
        # Render the pixel
        if self._cycle_x <= 256:
            self._render_pixel()

        # Update the state
        self._cycle_x += 1
        self._state = self.STORE_ATTRIBUTE

    def _store_attribute(self):
        """
        Store the attribute that was read.
        """
        # The low 12 bits of the attribute address are composed in the following way:
        #
        # NN 1111 YYY XXX
        # || |||| ||| +++-- high 3 bits of coarse X (x/4)
        # || |||| +++------ high 3 bits of coarse Y (y/4)
        # || ++++---------- attribute offset (960 bytes)
        # ++--------------- nametable select
        #
        # All credit for this explainer and the following line of code goes to:
        # https://wiki.nesdev.com/w/index.php/PPU_scrolling#Tile_and_attribute_fetching
        attribute_attr = (
            0x23C0
            | (self._vram_address & 0x0C00)
            | ((self._vram_address >> 4) & 0x38)
            | ((self._vram_address >> 2) & 0x07)
        ) & self._nametable_mirroring_mask

        attribute = self._memory[attribute_attr]

        # We're now going to compute the bits to select in the attribute byte.
        # The rendered screen is divided in 4x4 tile regions. Each of those tile regions
        # are further divided into 4 2x2 regions. Each pair of bits in the attribute
        # represent different 2x2 regions:
        # 0-1: Top left
        # 2-3: Top right
        # 4-5: Bottom left
        # 6-7: Bottom Right

        # We now need to find where the current tile fits in one the current 4x4 tile
        # region so we know which one of the four background palette will be used
        # for this tile.
        #
        # The coarse X and coarse Y coordinates indicate the tile index in the
        # grid we're pulling data from.
        #
        # The % 4 will tell us where in the 4x4 group a given tile is located.
        # This will remap values to 00 (0), 01 (1), 10 (2) or 11 (3). Shifting
        # right will yield 0 or 1, helping us chose in which horizontal and vertical
        # half of the 4x4 region this tile is.
        is_right = bool((self.coarse_x % 4) >> 1)
        is_bottom = bool((self.coarse_y % 4) >> 1)
        if is_right is False and is_bottom is False:
            self._attribute_bytes[self._current_tile_fetched] = attribute & 0b11
        elif is_right and is_bottom is False:
            self._attribute_bytes[self._current_tile_fetched] = attribute >> 2 & 0b11
        elif is_right is False and is_bottom:
            self._attribute_bytes[self._current_tile_fetched] = attribute >> 4 & 0b11
        else:
            self._attribute_bytes[self._current_tile_fetched] = attribute >> 6 & 0b11

        # Render the pixel
        if self._cycle_x <= 256:
            self._render_pixel()

        # Update the state
        self._cycle_x += 1
        self._state = self.FETCH_PATTERN_LOW

    def _fetch_pattern_low(self):
        """
        Retrieves the low pattern byte for rendering later.
        """
        # Render the pixel.
        if self._cycle_x <= 256:
            self._render_pixel()

        # We don't actually do anything here

        self._cycle_x += 1
        self._state = self.STORE_PATTERN_LOW

    def _store_pattern_low(self):
        """
        Stores the low pattern byte for rendering later.
        """
        # Read the byte from memory.
        self._pattern_low_bytes[self._current_tile_fetched] = self._pattern_table_memory[
            self._get_pattern_addr(False)
        ]

        # Render the pixel
        if self._cycle_x <= 256:
            self._render_pixel()

        # Update the state
        self._cycle_x += 1
        self._state = self.FETCH_PATTERN_HIGH

    def _fetch_pattern_high(self):
        """
        Retrieves the high pattern byte for rendering later.
        """
        # Render the pixel
        if self._cycle_x <= 256:
            self._render_pixel()

        # We don't actually do anything here

        # Update the state
        self._cycle_x += 1
        self._state = self.STORE_PATTERN_HIGH

    def _store_pattern_high(self):
        """
        Stores the high pattern byte for rendering later.
        """
        # Read the byte from memory.
        self._pattern_high_bytes[self._current_tile_fetched] = self._pattern_table_memory[
            self._get_pattern_addr(True)
        ]
        # We've now fetch all this tile's data, so increment the current tile fetched
        self._current_tile_fetched += 1

        # Render the pixel
        if self._cycle_x <= 256:
            self._render_pixel()

        if self._ppumask.is_rendering_enabled:
            # And increment the address to fetch from the nametable
            # if tile to fetch == 31
            # Credit for this logic goes to:
            # https://wiki.nesdev.com/w/index.php?title=PPU_scrolling&redirect=no#Coarse_X_increment
            if (self._vram_address & 0x001F) == 31:
                #  file to fetch = 0
                self._vram_address &= 0xFFE0
                # switch horizontal nametable
                self._vram_address ^= 0x0400
            else:
                # increment coarse X
                self._vram_address += 1

            # If we're on the last pixel of a visible scanline during rendering,
            # we need to adjust the vram address for the next read.
            # Credit for this logic goes to
            # https://wiki.nesdev.com/w/index.php/PPU_scrolling#Y_increment
            if self._cycle_x == 256 and (self._cycle_y < 240):
                # if fine Y < 7
                if (self._vram_address & 0x7000) != 0x7000:
                    # increment fine Y
                    self._vram_address += 0x1000
                else:
                    # fine Y = 0
                    self._vram_address &= 0x8FFF
                    # let y = coarse Y
                    y = (self._vram_address & 0x03E0) >> 5
                    if y == 29:
                        # coarse Y = 0
                        y = 0
                        # switch self._vertical nametable
                        self._vram_address ^= 0x0800
                    elif y == 31:
                        # coarse Y = 0, nametable not switched
                        y = 0
                    else:
                        # increment coarse Y
                        y += 1
                    # put coarse Y back into self._vram_address
                    self._vram_address = (self._vram_address & 0xFC1F) | (y << 5)

        self._cycle_x += 1
        if self._cycle_x == 257:
            self._state = self.LOAD_SPRITES
        elif self._cycle_x == 337:
            self._state = self.WASTE_NAMETABLE_BYTE
        else:
            self._state = self.FETCH_NAMETABLE

    def _waste_nametable_byte(self):
        """
        Each visible scanline finishes by reading a couple of bytes from the
        nametable and throwing them away. Once this state is completed
        we move to the beginning of the next scanline.
        """
        # TODO: Actually do the reads. It's not impossible some cartridge
        # hardware expects those reads to happen for syncing some operation.
        self._cycle_x += 1
        if (
            self._cycle_y == 261
            and self._cycle_x == 340
            and self._odd_frame
            and self._ppumask.is_rendering_enabled
        ):
            self._odd_frame = not self._odd_frame
            self._cycle_x = 0
            self._cycle_y = 0
            self._state = self.CYCLE_0
        elif self._cycle_x == 341:
            self._cycle_x = 0
            self._cycle_y += 1
            if self._cycle_y < 240:
                self._state = self.CYCLE_0
            elif self._cycle_y == 262:
                self._cycle_y = 0
                self._odd_frame = not self._odd_frame
                self._state = self.CYCLE_0
            else:
                self._state = self.POST_RENDER_SCANLINE

    def _post_render_scanline(self):
        """
        Nothing happens on this state as far as the PPU is concerned. The frame
        has been completely rendered, so we'll emit a frame completed event
        so the emulator can display the framebuffer contents.
        """
        # On the first cycle of the post render, raise a flag notifying that there is a frame ready.
        if self._cycle_x == 0:
            self._frame_ready_cb()
        self._cycle_x += 1
        if self._cycle_x == 341:
            self._cycle_x = 0
            self._cycle_y += 1
            self._state = self.FIRST_VBLANK_SCANLINE

    def _load_sprites(self):
        """
        Loads the sprite data.
        """
        if self._cycle_x == 257 and self._ppumask.is_rendering_enabled:
            self._update_x_scroll_bits()

            # TODO: Move this logic as a parallel process to the main state machine
            # for greater accuracy, but since we're focussed on getting the code up
            # and running, keep it simple for now.

            # Clear the sprite priority table, whatever happens on the next line, we don't
            # want to be caught using the previous lines tiles.
            for x in range(256):
                self._sprite_priority[x] = None

            next_line = self._cycle_y + 1

            # No need to read sprites for line 256, there is no next line.
            if self._ppumask.show_sprite is True and next_line < 239:
                current_sprite_index = 0

                # Read all of OAM memory and look for sprites that will be on the next scanline.
                for sprite_addr in range(0, 256, 4):

                    sprite_y = self._oam_memory[sprite_addr] + 1

                    # If the next line is above the top of the sprite or under it's bottom, skip it!
                    if next_line < sprite_y or next_line >= (
                        sprite_y + self._ppuctrl.sprite_height
                    ):
                        continue

                    # We've found one!
                    if current_sprite_index == 8:
                        # It's more complicated than that, but for now this might be good enough.
                        self._ppustatus.sprite_overflow = True
                        break

                    sprite = self.Sprite()

                    # We need to know if this is sprite zero, so we can test the sprite zero hit.
                    sprite.is_sprite_zero = sprite_addr == 0
                    # Extract pattern and attributes.
                    pattern_index = self._oam_memory[sprite_addr + 1]

                    sprite.attributes = self._oam_memory[sprite_addr + 2]

                    # Find on which line of the sprite the next rendered line will fall.
                    fine_y = next_line - sprite_y
                    # If the sprite if flipped.
                    if sprite.attributes & 0b10000000:
                        fine_y = (self._ppuctrl.sprite_height - 1) - fine_y

                    # Compute the address of the tile.
                    if self._ppuctrl.sprite_height == 8:
                        pattern_addr = (
                            self._ppuctrl.sprite_table_addr | fine_y | (pattern_index << 4)
                        )
                    else:
                        if fine_y <= 7:
                            pass
                        else:
                            fine_y += 8
                        pattern_addr = (
                            (pattern_index & 1) << 12 | ((pattern_index & 0xFE) * 16) | fine_y
                        )

                    # Loads the tile data
                    sprite.pattern_low = self._pattern_table_memory[pattern_addr]
                    sprite.pattern_high = self._pattern_table_memory[pattern_addr + 8]

                    sprite.left = self._oam_memory[sprite_addr + 3]

                    # IDEA: Try to compute the palette color right away,
                    # and save bg/foreground priority and if the pixel
                    # is part of sprite zero.
                    # This would mean we would compute the pixel's color
                    # only once and not dynamically allocate Sprite objects.
                    # If we keep making the logic more and more about bytes
                    # we might be able to cheat and turn it into Cython code?

                    # Find where this sprite lands on the scanline.
                    for x in range(sprite.left, min(sprite.left + 8, 255)):
                        # If the sprite is opaque on that line and it's not already occupied
                        # then mark it as having priority on this line.
                        if self._sprite_priority[x] is None and sprite.get_index(x):
                            self._sprite_priority[x] = sprite

                    current_sprite_index += 1

        # PPUOamAddr constantly gets wiped to zero here.
        self._ppuoamaddr.addr = 0

        self._cycle_x += 1
        if self._cycle_x == 321:
            # Start filling the latches with tile data.
            # The first bytes will be read at the beginning of this
            # scanline and more will be read by the time it ends.
            self._current_tile_fetched = 0
            self._state = self.FETCH_NAMETABLE

    def _first_vblank_scanline(self):
        """
        First vBlank scanline state will handle the state for the entire row and
        generate the interrupt on x cycle 1 and loop until the end of the
        scanline.
        """
        # On the first "pixel", the vblank flag is set and the
        # interupt is invoked if nmi is enabled.
        if self._cycle_x == 1:
            self._ppustatus.in_vblank = True
            if self._ppuctrl.generate_nmi:
                self._cpu.vblank_interrupt()

        self._cycle_x += 1
        if self._cycle_x == 341:
            self._cycle_x = 0
            self._cycle_y += 1
            self._state = self.IDLE_VBLANK_SCANLINES

    def _idle_vblank_scanlines(self):
        """
        These idle scanlines to nothing. They are simply an opportunity
        for the game to upload new sprite data and update the background.
        """
        self._cycle_x += 1
        if self._cycle_x == 341:
            self._cycle_x = 0
            self._cycle_y += 1
            if self._cycle_y == 261:
                self._state = self.PRE_RENDER_SCANLINE_START

    def _pre_render_scanline_start(self):
        """
        Pre-render scanline is responsible for resetting the vblank and sprite-0
        hit bits, reloading the x and y coordinates and loading the first two lines
        of scanline zero.

        For this state, we'll only concern ourselves with resetting the state and the
        x scroll bits.
        """
        if self._cycle_x == 1:
            self._ppustatus.in_vblank = False
            self._ppustatus.sprite_0_hit = False

        if self._cycle_x == 257 and self._ppumask.is_rendering_enabled:
            self._update_x_scroll_bits()

        self._cycle_x += 1

        if self._cycle_x == 280:
            # We only need to do this one on the pre-render scanline, doesn't really
            # matter when or in which state, so we're doing it here.
            # Clear the sprite priority table, whatever happens on the next line, we don't
            # want to be caught using the previous lines tiles.
            for x in range(256):
                self._sprite_priority[x] = None
            self._state = self.LOAD_VERTICAL_SCROLL

    def _load_vertical_scroll(self):
        """
        Reload the Y scroll bits from the temporary VRAM address to the VRAM address.
        During this stage, the Y scroll coordinate is reloaded in VRAM on each
        cycle.
        """
        if self._ppumask.is_rendering_enabled:
            self._vram_address = (self._vram_address & 0b000010000011111) | (
                self._tmp_vram_address & 0b0111101111100000
            )

        self._cycle_x += 1
        if self._cycle_x == 305:
            self._state = self.WAIT_FOR_SCANLINE_TILE_FETCH

    def _wait_for_scanline_tile_fetch(self):
        """
        Wait until the last stages of the pre-scanline, in which we'll start
        fetching tile data for scanline 0.
        """
        self._cycle_x += 1
        if self._cycle_x == 321:
            # Start filling the latches with tile data.
            self._current_tile_fetched = 0
            self._state = self.FETCH_NAMETABLE
