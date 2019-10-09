# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

import enum


class InterruptState(enum.IntEnum):
    """
    Interrupt state of the CPU.

    NONE means the CPU is not executing an interrupt, VBLANK means we're in VBLANK
    and RESET means the reset button was pressed.
    """

    NONE = 0
    VBLANK = 1
    RESET = 2


class CPU:
    """
    Brain of the emulator. You can call emulate to execute an instruction.

    The CPU communicates via the various devices through the :class:`MemoryBus`.
    """

    __slots__ = [
        ############################################################################################
        # These are the CPU registers
        "_accumulator",
        "_index_x",
        "_index_y",
        "_program_counter",
        "_stack_pointer",
        ############################################################################################
        # Status register bits
        "_carry_flag",
        "_zero_flag",
        "_interrupt_disabled_flag",
        # This flag is implemented, but the NES CPU doesn't support decimal mode
        "_decimal_mode_flag",
        "_overflow_flag",
        "_negative_flag",
        ############################################################################################
        # Miscellaneous
        "_memory_bus",
        "_ppu",
        # The _opcodes array holds a list of callables that are going to be
        # called for each instruction.
        "_opcodes",
        # Clock cycles are not calculated at the end of the instruction, but
        # actually during the execution of the CPU instruction themselves,
        # allowing a greater emulation accuracy, which some games require.
        # Essentially, every single read/write operation makes the CPU tick by a
        # cycle. Then some instructions have some internal lag as well.
        "_nb_cycles",
        # Interrupt state is a flag that indicates the current interrupt.
        "_interrupt_state",
    ]

    def __init__(self, ppu, memory_bus):
        """
        :param emnes.MemoryBus memory_bus: Bus the CPU will use to read and
            write memory.
        """
        self._memory_bus = memory_bus
        self._memory_bus.cpu = self
        self._ppu = ppu
        self._ppu.cpu = self

        self._carry_flag = False
        self._zero_flag = False
        self._interrupt_disabled_flag = True
        self._decimal_mode_flag = False
        self._overflow_flag = False
        self._negative_flag = False

        self._accumulator = 0
        self._index_x = 0
        self._index_y = 0

        self._stack_pointer = 0xFD
        self._program_counter = (
            self._memory_bus.read_byte(0xFFFC) | self._memory_bus.read_byte(0xFFFD) << 8
        )
        self._nb_cycles = 0

        self._interrupt_state = InterruptState.NONE

        self._init_opcodes()

    def _init_opcodes(self):
        """
        Initializes the opcodes array.
        """

        # Allocate room for all the opcodes.
        # Prefill the array with unknown opcodes functors. We'll them replace
        # them with real instructions.
        self._opcodes = list(lambda: self._unknown_opcode(i) for i in range(256))

        # NOP
        self._opcodes[0xEA] = self._nop

        # Break
        self._opcodes[0x00] = self._break

        ############################################################################################
        # Status register modifiers
        self._opcodes[0x78] = lambda: self._set_interrupt_disable_flag(True)
        self._opcodes[0x58] = lambda: self._set_interrupt_disable_flag(False)
        self._opcodes[0xF8] = lambda: self._set_decimal_mode_flag(True)
        self._opcodes[0xD8] = lambda: self._set_decimal_mode_flag(False)
        self._opcodes[0x18] = lambda: self._set_carry_flag(False)
        self._opcodes[0x38] = lambda: self._set_carry_flag(True)
        self._opcodes[0xB8] = lambda: self._set_overflow_flag(False)

        ############################################################################################
        # Stack related operations
        self._opcodes[0x28] = self._pop_status_register
        self._opcodes[0x08] = self._push_status_register
        # Waste a cycle reading and the push the byte.
        self._opcodes[0x48] = self._push_accumulator
        self._opcodes[0x68] = self._pop_accumulator

        ############################################################################################
        # Jump instructions
        self._opcodes[0x4C] = lambda: self._jump(self._absolute())
        self._opcodes[0x6C] = lambda: self._jump(self._absolute_jump_address())
        self._opcodes[0x20] = self._jump_to_subroutine
        self._opcodes[0x60] = self._jump_from_subroutine
        self._opcodes[0x40] = self._return_from_interrupt

        ############################################################################################
        # Store operands
        # Y -> Memory
        self._opcodes[0x84] = lambda: self._write_byte(self._zero_page(), self._index_y)
        self._opcodes[0x94] = lambda: self._write_byte(self._zero_page_x(), self._index_y)
        self._opcodes[0x8C] = lambda: self._write_byte(self._absolute(), self._index_y)

        # X -> Memory
        self._opcodes[0x86] = lambda: self._write_byte(self._zero_page(), self._index_x)
        self._opcodes[0x96] = lambda: self._write_byte(self._zero_page_y(), self._index_x)
        self._opcodes[0x8E] = lambda: self._write_byte(self._absolute(), self._index_x)

        # Accumulator -> Memory
        self._opcodes[0x85] = lambda: self._write_byte(self._zero_page(), self._accumulator)
        self._opcodes[0x95] = lambda: self._write_byte(self._zero_page_x(), self._accumulator)
        self._opcodes[0x8D] = lambda: self._write_byte(self._absolute(), self._accumulator)
        self._opcodes[0x9D] = lambda: self._write_byte(self._absolute_x_write(), self._accumulator)
        self._opcodes[0x99] = lambda: self._write_byte(self._absolute_y_write(), self._accumulator)
        self._opcodes[0x81] = lambda: self._write_byte(self._indirect_x(), self._accumulator)
        self._opcodes[0x91] = lambda: self._write_byte(self._indirect_y_write(), self._accumulator)

        ############################################################################################
        # Loads opcodes
        # Accumulator <- X|Y|Memory
        self._opcodes[0x98] = self._tya
        self._opcodes[0x8A] = self._txa
        self._opcodes[0xA9] = lambda: self._lda(self._immediate())
        self._opcodes[0xA5] = lambda: self._lda(self._zero_page())
        self._opcodes[0xB5] = lambda: self._lda(self._zero_page_x())
        self._opcodes[0xAD] = lambda: self._lda(self._absolute())
        self._opcodes[0xBD] = lambda: self._lda(self._absolute_x())
        self._opcodes[0xB9] = lambda: self._lda(self._absolute_y())
        self._opcodes[0xA1] = lambda: self._lda(self._indirect_x())
        self._opcodes[0xB1] = lambda: self._lda(self._indirect_y())

        # Y <- Memory|Accumulator
        self._opcodes[0xA0] = lambda: self._ldy(self._immediate())
        self._opcodes[0xA4] = lambda: self._ldy(self._zero_page())
        self._opcodes[0xB4] = lambda: self._ldy(self._zero_page_x())
        self._opcodes[0xAC] = lambda: self._ldy(self._absolute())
        self._opcodes[0xBC] = lambda: self._ldy(self._absolute_x())
        self._opcodes[0xA8] = self._tay

        # X <- Memory|Accumulator|Stack Pointer
        self._opcodes[0xA2] = lambda: self._ldx(self._immediate())
        self._opcodes[0xA6] = lambda: self._ldx(self._zero_page())
        self._opcodes[0xB6] = lambda: self._ldx(self._zero_page_y())
        self._opcodes[0xAE] = lambda: self._ldx(self._absolute())
        self._opcodes[0xBE] = lambda: self._ldx(self._absolute_y())
        self._opcodes[0xAA] = self._tax
        self._opcodes[0xBA] = self._tsx

        # SP <- X
        self._opcodes[0x9A] = self._txs

        ############################################################################################
        # Branching
        self._opcodes[0xD0] = lambda: self._branch_if(not self._zero_flag)
        self._opcodes[0xF0] = lambda: self._branch_if(self._zero_flag)
        self._opcodes[0x90] = lambda: self._branch_if(not self._carry_flag)
        self._opcodes[0xB0] = lambda: self._branch_if(self._carry_flag)
        self._opcodes[0x10] = lambda: self._branch_if(not self._negative_flag)
        self._opcodes[0x30] = lambda: self._branch_if(self._negative_flag)
        self._opcodes[0x50] = lambda: self._branch_if(not self._overflow_flag)
        self._opcodes[0x70] = lambda: self._branch_if(self._overflow_flag)

        ############################################################################################
        # Bitwise operators
        # Bit testing
        self._opcodes[0x24] = lambda: self._bit(self._zero_page())
        self._opcodes[0x2C] = lambda: self._bit(self._absolute())

        # Shift left
        self._opcodes[0x0A] = lambda: self._rmw_accumulator(self._asl)
        self._opcodes[0x06] = lambda: self._rmw_memory(self._zero_page(), self._asl)
        self._opcodes[0x16] = lambda: self._rmw_memory(self._zero_page_x(), self._asl)
        self._opcodes[0x0E] = lambda: self._rmw_memory(self._absolute(), self._asl)
        self._opcodes[0x1E] = lambda: self._rmw_memory(self._absolute_x_write(), self._asl)

        # Shift right
        self._opcodes[0x4A] = lambda: self._rmw_accumulator(self._logical_shift_right)
        self._opcodes[0x46] = lambda: self._rmw_memory(self._zero_page(), self._logical_shift_right)
        self._opcodes[0x56] = lambda: self._rmw_memory(
            self._zero_page_x(), self._logical_shift_right
        )
        self._opcodes[0x4E] = lambda: self._rmw_memory(self._absolute(), self._logical_shift_right)
        self._opcodes[0x5E] = lambda: self._rmw_memory(
            self._absolute_x_write(), self._logical_shift_right
        )

        # Rotate left
        self._opcodes[0x2A] = lambda: self._rmw_accumulator(self._rotate_left)
        self._opcodes[0x26] = lambda: self._rmw_memory(self._zero_page(), self._rotate_left)
        self._opcodes[0x36] = lambda: self._rmw_memory(self._zero_page_x(), self._rotate_left)
        self._opcodes[0x2E] = lambda: self._rmw_memory(self._absolute(), self._rotate_left)
        self._opcodes[0x3E] = lambda: self._rmw_memory(self._absolute_x_write(), self._rotate_left)

        # Rotate Right
        self._opcodes[0x6A] = lambda: self._rmw_accumulator(self._rotate_right)
        self._opcodes[0x66] = lambda: self._rmw_memory(self._zero_page(), self._rotate_right)
        self._opcodes[0x76] = lambda: self._rmw_memory(self._zero_page_x(), self._rotate_right)
        self._opcodes[0x6E] = lambda: self._rmw_memory(self._absolute(), self._rotate_right)
        self._opcodes[0x7E] = lambda: self._rmw_memory(self._absolute_x_write(), self._rotate_right)

        # OR
        self._opcodes[0x09] = lambda: self._ora(self._immediate())
        self._opcodes[0x05] = lambda: self._ora(self._zero_page())
        self._opcodes[0x15] = lambda: self._ora(self._zero_page_x())
        self._opcodes[0x0D] = lambda: self._ora(self._absolute())
        self._opcodes[0x1D] = lambda: self._ora(self._absolute_x())
        self._opcodes[0x19] = lambda: self._ora(self._absolute_y())
        self._opcodes[0x01] = lambda: self._ora(self._indirect_x())
        self._opcodes[0x11] = lambda: self._ora(self._indirect_y())

        # Exclusive OR
        self._opcodes[0x49] = lambda: self._eor(self._immediate())
        self._opcodes[0x45] = lambda: self._eor(self._zero_page())
        self._opcodes[0x55] = lambda: self._eor(self._zero_page_x())
        self._opcodes[0x4D] = lambda: self._eor(self._absolute())
        self._opcodes[0x5D] = lambda: self._eor(self._absolute_x())
        self._opcodes[0x59] = lambda: self._eor(self._absolute_y())
        self._opcodes[0x41] = lambda: self._eor(self._indirect_x())
        self._opcodes[0x51] = lambda: self._eor(self._indirect_y())

        # AND
        self._opcodes[0x29] = lambda: self._and(self._immediate())
        self._opcodes[0x25] = lambda: self._and(self._zero_page())
        self._opcodes[0x35] = lambda: self._and(self._zero_page_x())
        self._opcodes[0x2D] = lambda: self._and(self._absolute())
        self._opcodes[0x3D] = lambda: self._and(self._absolute_x())
        self._opcodes[0x39] = lambda: self._and(self._absolute_y())
        self._opcodes[0x21] = lambda: self._and(self._indirect_x())
        self._opcodes[0x31] = lambda: self._and(self._indirect_y())

        ############################################################################################
        # Arithmetic
        # Increment
        self._opcodes[0xE6] = lambda: self._rmw_memory(self._zero_page(), self._increment)
        self._opcodes[0xF6] = lambda: self._rmw_memory(self._zero_page_x(), self._increment)
        self._opcodes[0xEE] = lambda: self._rmw_memory(self._absolute(), self._increment)
        self._opcodes[0xFE] = lambda: self._rmw_memory(self._absolute_x_write(), self._increment)
        self._opcodes[0xE8] = lambda: self._rmw_index_x(self._increment)
        self._opcodes[0xC8] = lambda: self._rmw_index_y(self._increment)

        # Decrement
        self._opcodes[0xCA] = lambda: self._rmw_index_x(self._decrement)
        self._opcodes[0x88] = lambda: self._rmw_index_y(self._decrement)
        self._opcodes[0xC6] = lambda: self._rmw_memory(self._zero_page(), self._decrement)
        self._opcodes[0xD6] = lambda: self._rmw_memory(self._zero_page_x(), self._decrement)
        self._opcodes[0xCE] = lambda: self._rmw_memory(self._absolute(), self._decrement)
        self._opcodes[0xDE] = lambda: self._rmw_memory(self._absolute_x_write(), self._decrement)

        # Compare
        self._opcodes[0xE0] = lambda: self._cmp(self._index_x, self._immediate())
        self._opcodes[0xE4] = lambda: self._cmp(self._index_x, self._zero_page())
        self._opcodes[0xEC] = lambda: self._cmp(self._index_x, self._absolute())
        self._opcodes[0xC0] = lambda: self._cmp(self._index_y, self._immediate())
        self._opcodes[0xC4] = lambda: self._cmp(self._index_y, self._zero_page())
        self._opcodes[0xCC] = lambda: self._cmp(self._index_y, self._absolute())
        self._opcodes[0xC9] = lambda: self._cmp(self._accumulator, self._immediate())
        self._opcodes[0xC5] = lambda: self._cmp(self._accumulator, self._zero_page())
        self._opcodes[0xD5] = lambda: self._cmp(self._accumulator, self._zero_page_x())
        self._opcodes[0xCD] = lambda: self._cmp(self._accumulator, self._absolute())
        self._opcodes[0xDD] = lambda: self._cmp(self._accumulator, self._absolute_x())
        self._opcodes[0xD9] = lambda: self._cmp(self._accumulator, self._absolute_y())
        self._opcodes[0xC1] = lambda: self._cmp(self._accumulator, self._indirect_x())
        self._opcodes[0xD1] = lambda: self._cmp(self._accumulator, self._indirect_y())

        # Add
        self._opcodes[0x69] = lambda: self._adc(self._immediate())
        self._opcodes[0x65] = lambda: self._adc(self._zero_page())
        self._opcodes[0x75] = lambda: self._adc(self._zero_page_x())
        self._opcodes[0x6D] = lambda: self._adc(self._absolute())
        self._opcodes[0x7D] = lambda: self._adc(self._absolute_x())
        self._opcodes[0x79] = lambda: self._adc(self._absolute_y())
        self._opcodes[0x61] = lambda: self._adc(self._indirect_x())
        self._opcodes[0x71] = lambda: self._adc(self._indirect_y())

        # Substract
        self._opcodes[0xE9] = lambda: self._sbc(self._immediate())
        self._opcodes[0xE5] = lambda: self._sbc(self._zero_page())
        self._opcodes[0xF5] = lambda: self._sbc(self._zero_page_x())
        self._opcodes[0xED] = lambda: self._sbc(self._absolute())
        self._opcodes[0xFD] = lambda: self._sbc(self._absolute_x())
        self._opcodes[0xF9] = lambda: self._sbc(self._absolute_y())
        self._opcodes[0xE1] = lambda: self._sbc(self._indirect_x())
        self._opcodes[0xF1] = lambda: self._sbc(self._indirect_y())

    def __getstate__(self):
        """
        Captures the state of the CPU. Used when pickling.

        :returns: `dict` of the state.
        """
        # The opcodes list can't be pickled because _opcodes are lambdas which are not
        # pickle-able it seems.
        return {slot: getattr(self, slot) for slot in self.__slots__ if slot != "_opcodes"}

    def __setstate__(self, state):
        """
        Restores the state of the CPU. Use when unpickling.

        :param dict state: State captured by __getstate__.
        """
        for k, v in state.items():
            setattr(self, k, v)
        # Restore opcodes array that couldn't be pickled.
        self._init_opcodes()

    def emulate(self):
        """
        Emulate one instruction.

        In an interrupt was raised, the program counter will be updated with the
        right address from the interrupt vector at 0xFFFA-0xFFFF instead of executing
        the next operation.

        :returns: Number of cycles elapsed.
        """
        nb_cycles_before = self._nb_cycles
        if self._interrupt_state == InterruptState.NONE:
            self._opcodes[self._read_code_byte()]()
        elif self._interrupt_state == InterruptState.VBLANK:
            # CPU wastes a cycle reading the next instruction
            self._read_byte(self._program_counter)
            self._handle_interrupt(0xFFFA)
            self._interrupt_state = InterruptState.NONE
        return self._nb_cycles - nb_cycles_before

    def vblank_interrupt(self):
        """
        Raises the VBLANK interrupt flag.

        One the next call to emulate, the program counter will be updated with the
        address stored at 0xFFFA-0xFFFB.
        """
        self._interrupt_state = InterruptState.VBLANK

    def dma_transfer(self, address_high):
        """
        Executes a DMA transfer.

        :param int address_high: High byte of the address to launch a DMA transfer
                                 to the OAM memory.
        """
        # There's one extra tick for waiting for writes to finish
        self._tick()
        # Then one other extra tick on odd CPU cycles.
        if self._nb_cycles % 2 == 1:
            self._tick()
        # Then 512 cycles are spent copying data around. Using write_byte
        # read_byte will count those 512 cycles for us.
        start = address_high << 8
        for addr in range(start, start + 256):
            # Hardware wise this actually implemented as 256 writes to the
            # PPUOAMDATA register (0x2004), so do the same.
            self._write_byte(0x2004, self._read_byte(addr))

    def _handle_interrupt(self, interrupt_addr):
        """
        Push the program counter and status bits and jump to the location
        stored at the given address.

        There are three interrupt types: reset, vblank and break.

        :param int interrupt_addr: Address of interrupt vector index to load and
                                   jump to.
        """
        # Push the state of the program counter and status register
        self._push_word(self._program_counter)
        self._push_byte(self.status | 0b00010000)

        # Update the program counter.
        self._program_counter = self._read_word(interrupt_addr)
        self._interrupt_disabled_flag = True

    def _tick(self):
        """
        Executes a CPU tick, which increments the number of cycles by 1.
        """
        self._nb_cycles += 1

    ################################################################################################
    # Accessors for the registers

    @property
    def nb_cycles(self):
        """
        Number of cycles elapsed since the start.
        """
        return self._nb_cycles

    @nb_cycles.setter
    def nb_cycles(self, nb_cycles):
        """
        Set the number of cycles elapsed since the start.
        """
        self._nb_cycles = nb_cycles

    @property
    def program_counter(self):
        """
        Access the program counter.
        """
        return self._program_counter

    @program_counter.setter
    def program_counter(self, program_counter):
        """
        Access the program counter.
        """
        self._program_counter = program_counter & 0xFFFF

    @property
    def accumulator(self):
        """
        Access the accumulator.
        """
        return self._accumulator

    @property
    def index_x(self):
        """
        Access the X register.
        """
        return self._index_x

    @property
    def index_y(self):
        """
        Access the Y register.
        """
        return self._index_y

    @property
    def stack_pointer(self):
        """
        Access the stack pointer.
        """
        return self._stack_pointer

    @stack_pointer.setter
    def stack_pointer(self, stack_pointer):
        """
        Access the stack pointer.
        """
        self._stack_pointer = stack_pointer & 0xFF

    @property
    def status(self):
        """
        Access the status flag.
        """
        # The status flag is always read with bit 6 set
        return (
            int(self._carry_flag)
            | (int(self._zero_flag) << 1)
            | (int(self._interrupt_disabled_flag) << 2)
            | (int(self._decimal_mode_flag) << 3)
            | (1 << 5)
            | (int(self._overflow_flag) << 6)
            | (int(self._negative_flag) << 7)
        )

    def reset(self):
        """
        Reset the CPU and jumps to the address referred by the interrupt vector at 0xFFFX.
        """
        # Do not call the _handle_interrupt routine here. The CPU doesn't actually
        # write to the RAM the values upon reset.
        # https://wiki.nesdev.com/w/index.php/CPU_power_up_state
        self._stack_pointer = (self._stack_pointer - 3) & 0xFF
        self._interrupt_disabled_flag = True
        self._program_counter = self._read_word(0xFFFC)

    def _read_code_byte(self):
        """
        Fetch one byte and moves the program counter forward by one byte.

        :returns: The byte that was read.
        :rtype: int
        """
        byte = self._read_byte(self._program_counter)
        self._program_counter += 1
        return byte

    def _read_code_word(self):
        """
        Fetch two bytes and moves the program counter forward by two bytes.

        Given the bytes in the memory laid out as 0xAA 0xBB, the resulting
        word will be 0xBBAA, as the CPU is little endian.

        :returns: The word that was read.
        :rtype: int
        """
        return self._read_code_byte() | (self._read_code_byte() << 8)

    def _read_byte(self, addr):
        """
        Read a byte from memory.

        :param int addr: Address to read from.

        :returns: The read byte.
        """
        value = self._memory_bus.read_byte(addr)
        self._tick()
        return value

    def _write_byte(self, addr, value):
        """
        Write a byte to memory.

        :param int addr: Address to write to.
        :param int value: Value to write.
        """
        self._memory_bus.write_byte(addr, value)
        self._tick()

    def _read_word(self, addr):
        """
        Read a word from memory.

        :param int addr: Address to read from.

        :returns: The read word.
        """
        return self._read_byte(addr) | (self._read_byte(addr + 1) << 8)

    ############################################################################
    # The following methods compute the address referred by the operand.

    # _zero_page would simply pass-through to _read_core_byte, so alias the
    # method name so we save one function call, which are expensive.
    _zero_page = _read_code_byte

    def _immediate(self):
        """
        Compute the immediate address, i.e. address of the program counter

        :returns: Program Counter value.
        """
        pc = self._program_counter
        self._program_counter += 1
        return pc

    def _zero_page_x(self):
        """
        Compute a memory address by adding the value of the next byte + X.

        :returns: Address between 0 and 255.
        """
        base = self._zero_page()
        # waste a read cycle at the wrong locatiom
        self._tick()
        return (base + self._index_x) & 0xFF

    def _zero_page_y(self):
        """
        Compute a memory address by adding the value of the next byte + Y.

        :returns: Address between 0 and 255.
        """
        base = self._zero_page()
        # wastes a cycle reading at base
        self._tick()
        return (base + self._index_y) & 0xFF

    # _absolute would simply pass-through to _read_code_word, so alias the
    # method name so we save one function call, which are expensive.
    _absolute = _read_code_word

    def _absolute_jump_address(self):
        """
        Compute the jump address found at the memory location found by reading the memory referred
        by the next two bytes.

        :returns: Address between 0 and 65535.
        """
        addr = self._read_code_word()
        first_addr = addr
        # There's a bug in the 6502 when fetching the
        # address on a page boundary. It reads
        # the second byte at the beginning of the current page
        # instead of the next one.
        if addr & 0xFF == 0xFF:
            second_addr = addr & 0xFF00
        else:
            second_addr = addr + 1
        return self._read_byte(first_addr) | (self._read_byte(second_addr) << 8)

    def _absolute_x(self):
        """
        Compute memory address taken from the next word + index x.

        :returns: Address between 0 and 65535.
        """
        src = self._absolute()
        dst = (src + self._index_x) & 0xFFFF
        if self._is_new_page(src, dst):
            self._tick()
        return dst

    def _absolute_x_write(self):
        """
        Compute memory address taken from the next word + index x during a write.

        :returns: Address between 0 and 65535.
        """
        src = self._absolute()
        dst = (src + self._index_x) & 0xFFFF
        # During a write, we always tick, whether this is a new page or not.
        self._tick()
        return dst

    def _absolute_y(self):
        """
        Compute memory address taken from the next word + index y.

        :returns: Address between 0 and 65535.
        """
        src = self._absolute()
        dst = (src + self._index_y) & 0xFFFF
        if self._is_new_page(src, dst):
            self._tick()
        return dst

    def _absolute_y_write(self):
        """
        Compute memory address taken from the next word + index y during a write.

        :returns: Address between 0 and 65535.
        """
        src = self._absolute()
        dst = (src + self._index_y) & 0xFFFF
        # During a write, we always tick, whether this is a new page or not.
        self._tick()
        return dst

    def _indirect(self):
        """
        Compute memory address taken at the address referred by the next word.

        :returns: Address between 0 and 65535.
        """
        return self._read_word(self._absolute())

    def _indirect_x(self):
        """
        Retrieve address in memory found at the zero page x address.

        :returns: Address between 0 and 65535.
        """
        addr = self._zero_page_x()
        return self._read_byte(addr) | (self._read_byte((addr + 1) & 0xFF) << 8)

    def _indirect_y(self):
        """
        Retrieve address in memory found at the zero page address and
        adds the y offset.

        :returns: Address between 0 and 65535.
        """
        addr = self._zero_page()
        src = self._read_byte(addr) | (self._read_byte((addr + 1) & 0xFF) << 8)
        dst = (src + self._index_y) & 0xFFFF
        if self._is_new_page(src, dst):
            self._tick()

        return dst

    def _indirect_y_write(self):
        """
        Retrieve address in memory found at the zero page address and
        adds the y offset during a write.

        :returns: Address between 0 and 65535.
        """
        addr = self._zero_page()
        src = self._read_byte(addr) | (self._read_byte((addr + 1) & 0xFF) << 8)
        dst = (src + self._index_y) & 0xFFFF

        # During a write, we always tick, whether this is a new page or not.
        self._tick()
        return dst

    def _relative(self):
        """
        Retrieve a signed address offset from the next byte.

        :returns: Offset between -128 and 127.
        """
        value = self._read_code_byte()
        if value <= 127:
            return value
        else:
            return -256 + value

    ############################################################################
    # The following methods operate on the stack.

    def _push_byte(self, value):
        """
        Push a byte on the stack.

        :param int value: Value to push on the stack.
        """
        self._write_byte((self._stack_pointer + 0x100), value)
        self._stack_pointer = (self._stack_pointer - 1) & 0xFF

    def _push_word(self, value):
        """
        Push a word on the stack.

        :param int value: Value to push on the stack.
        """
        self._push_byte(value >> 8)
        self._push_byte(value & 0xFF)

    def _increment_stack_pointer(self):
        """
        Increments the stack pointer by 1.
        """
        self._stack_pointer = (self._stack_pointer + 1) & 0xFF

    def _read_stack_top(self):
        """
        Reads the value at the top of the stack.

        :returns: The top byte.
        """
        return self._read_byte(self._stack_pointer + 0x100)

    ############################################################################
    # The following emulates the CPU opcodes

    def _break(self):
        """
        Save the current program counter and status register and jump to the
        interrupt handler address read from 0xFEEE
        """
        # Break eats the next byte, which means that it effectively jumps over
        # the next one byte instruction.
        self._read_code_byte()
        self._handle_interrupt(0xFFFE)

    def _nop(self):
        """
        Nop. It ticks!
        """
        self._tick()

    def _set_interrupt_disable_flag(self, value):
        """
        Set the interrupt disable flag.

        :param bool value: Value to set the flag.
        """
        self._interrupt_disabled_flag = value
        self._tick()

    def _set_carry_flag(self, value):
        """
        Set the carry flag.

        :param bool value: Value to set the flag.
        """
        self._carry_flag = value
        self._tick()

    def _set_overflow_flag(self, value):
        """
        Set the overflow flag.

        :param bool value: Value to set the flag.
        """
        self._overflow_flag = value
        self._tick()

    def _set_decimal_mode_flag(self, value):
        """
        Set the decimal mode flag.

        :param bool value: Value to set the flag.
        """
        self._decimal_mode_flag = value
        self._tick()

    def _pop_status_register(self):
        """
        Pop the status register from the stack.
        """
        self._tick()

        self._increment_stack_pointer()
        self._tick()

        self._update_status_register(self._read_stack_top())

    def _update_status_register(self, value):
        """
        Update the status flags with the given value.

        It decomposes the byte into a set of booleans.

        :param int value: Value of the flag register.
        """
        self._carry_flag = bool(value & 0x1)
        self._zero_flag = bool(value & 0x2)
        self._interrupt_disabled_flag = bool(value & 0x4)
        self._decimal_mode_flag = bool(value & 0x8)
        self._overflow_flag = bool(value & 0x40)
        self._negative_flag = bool(value & 0x80)

    def _push_status_register(self):
        """
        Push the status register on the stack.
        """
        # The two unused bits are always pushed as set.
        self._tick()
        self._push_byte(self.status | 0b00010000)

    def _push_accumulator(self):
        """
        Push the accumulator on the stack.
        """
        # Waste a cycle reading a byte.
        self._tick()
        self._push_byte(self._accumulator)

    def _pop_accumulator(self):
        """
        Pops the accumulator from the stack.
        """
        # Waste a cycle reading a byte.
        self._tick()

        self._increment_stack_pointer()
        self._tick()

        self._load_accumulator(self._read_stack_top())

    def _jump(self, addr):
        """
        Update the program counter to the passed in address.

        :param int addr: Address to jump to.
        """
        self._program_counter = addr

    def _jump_to_subroutine(self):
        """
        Jump to the memory location referred by the next word.

        Pushes the return address on stack first.
        """
        pcl = self._read_code_byte()
        # Waste a cycle
        self._tick()
        self._push_word(self._program_counter)
        pch = self._read_code_byte()
        self._program_counter = pcl | (pch << 8)

    def _jump_from_subroutine(self):
        """
        Jump to the memory location at the top of the stack.
        """
        # waste a read
        self._tick()

        self._increment_stack_pointer()
        self._tick()

        pcl = self._read_stack_top()
        self._increment_stack_pointer()

        pch = self._read_stack_top()

        self._program_counter = pcl | (pch << 8)
        self._program_counter += 1
        self._tick()

    def _return_from_interrupt(self):
        """
        Pop the status register and program counter from the stack.
        """
        # CPU wastes one cycle reading the next byte.
        self._tick()

        self._increment_stack_pointer()
        self._tick()

        self._update_status_register(self._read_stack_top())
        self._increment_stack_pointer()

        pcl = self._read_stack_top()
        self._increment_stack_pointer()

        pch = self._read_stack_top()

        self._program_counter = pcl | (pch << 8)

    def _load_index_x(self, value):
        """
        Load value into register x.

        :param value: Value to load into x.
        """
        self._index_x = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)

    def _ldx(self, addr):
        """
        Load value at a given address into x.

        :param int addr: Address to load value into.
        """
        value = self._read_byte(addr)
        self._index_x = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)

    def _tax(self):
        """
        Transfer accumulator into x.
        """
        self._load_index_x(self._accumulator)
        self._tick()

    def _tsx(self):
        """
        Transfer x into stack pointer.
        """
        self._load_index_x(self._stack_pointer)
        self._tick()

    def _load_index_y(self, value):
        """
        Load value into register y.

        :param int value: Value to load.
        """
        self._index_y = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)

    def _ldy(self, addr):
        """
        Load value into register y.

        :param int value: Value to load.
        """
        value = self._read_byte(addr)
        self._index_y = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)

    def _tay(self):
        """
        Transfer accumulator into y.
        """
        self._load_index_y(self._accumulator)
        self._tick()

    def _tya(self):
        """
        Transfer y into accumulator.
        """
        self._load_accumulator(self._index_y)
        self._tick()

    def _txa(self):
        """
        Transfer x into accumulator.
        """
        self._load_accumulator(self._index_x)
        self._tick()

    def _load_accumulator(self, value):
        """
        Load value into accumulator

        :param int value: Value to load.
        """
        self._accumulator = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)

    def _lda(self, addr):
        """
        Loads a byte from memory into accumulator.

        :param int addr: Address to read the byte from.
        """
        value = self._read_byte(addr)
        self._accumulator = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)

    def _txs(self):
        """
        Load X into stack pointer.
        """
        self._stack_pointer = self._index_x
        self._tick()

    def _branch_if(self, should_branch):
        """
        Offset the program counter by to the relative address read from memory
        if the passed in flag is ``True``.

        :param bool should_branch: Flag value to test.
        """
        # Read the operand first before testing to make sure
        # the program counter is updated.
        offset = self._relative()
        if should_branch:
            self._tick()
            destination = self._program_counter + offset
            if self._is_new_page(self._program_counter, destination):
                self._tick()
            self._program_counter = destination

    def _is_new_page(self, src, dest):
        """
        Compare addresses to see if the destination is a new page.

        :param int src: Source address
        :param int dest: Destination address

        :returns: ``True`` if the src and dest are on different pages, ``False``
            otherwise.
        """
        return (src & 0xFF00) != (dest & 0xFF00)

    def _bit(self, addr):
        """
        Test the overflow and negative bit and zero value of the passed in value.

        :param int value: Value to test.
        """
        value = self._read_byte(addr)
        self._overflow_flag = bool(value & 0b01000000)
        self._negative_flag = bool(value & 0b10000000)
        self._zero_flag = not (self._accumulator & value)

    def _asl(self, value):
        """
        Shift bits from the passed in value left.

        This is usually used during a read-modify-write instruction.

        :param int value: Value to shift

        :returns: The shifted value.
        """
        self._carry_flag = bool(value & 0x80)
        result = (value << 1) & 0xFF
        self._zero_flag = not result
        self._negative_flag = bool(result & 0x80)
        return result

    def _logical_shift_right(self, value):
        """
        Shift bits from value right.

        This is usually used during a read-modify-write instruction.

        :param int value: Value to shift.

        :returns: Shifted value.
        """
        self._carry_flag = bool(value & 0x1)
        result = value >> 1
        self._zero_flag = not result
        self._negative_flag = bool(result & 0x80)
        return result

    def _rotate_left(self, value):
        """
        Rotate bits from the passed in value left.

        This is usually used during a read-modify-write instruction.

        :param int value: Value to rotate

        :returns: The rotated value.
        """
        result = ((value << 1) & 0xFF) | int(self._carry_flag)
        self._carry_flag = bool(value & 0x80)
        self._zero_flag = not result
        self._negative_flag = bool(result & 0x80)
        return result

    def _rotate_right(self, value):
        """
        Rotate bits from the passed in value right.

        This is usually used during a read-modify-write instruction.

        :param int value: Value to rotate

        :returns: The rotated value.
        """
        result = (value >> 1) | (int(self._carry_flag) << 7)
        self._carry_flag = bool(value & 0x1)
        self._zero_flag = not result
        self._negative_flag = bool(result & 0x80)
        return result

    def _ora(self, addr):
        """
        Update the accumulator with the result of accumulator | value

        :param int value: Value to or with.
        """
        value = self._read_byte(addr)
        self._accumulator = self._accumulator | value
        self._zero_flag = not self._accumulator
        self._negative_flag = bool(self._accumulator & 0x80)

    def _eor(self, addr):
        """
        Update the accumulator with the result of accumulator ^ value

        :param int value: Value to exclusive or with.
        """
        value = self._read_byte(addr)
        self._accumulator = self._accumulator ^ value
        self._zero_flag = not self._accumulator
        self._negative_flag = bool(self._accumulator & 0x80)

    def _and(self, addr):
        """
        Update the accumulator with the result of accumulator & value

        :param int value: Value to and with.
        """
        value = self._read_byte(addr)
        self._accumulator = self._accumulator & value
        self._zero_flag = not self._accumulator
        self._negative_flag = bool(self._accumulator & 0x80)

    def _increment(self, value):
        """
        Increment a value and returns the result.

        This is usually used during a read-modify-write instruction.

        :param int value: Value to increment.

        :returns: The incremened value.
        """
        result = (value + 1) & 0xFF
        self._zero_flag = not result
        self._negative_flag = bool(result & 0x80)
        return result

    def _decrement(self, value):
        """
        Decrement a value and returns the result.

        This is usually used during a read-modify-write instruction.

        :param int value: Value to decrement.

        :returns: The decremented value.
        """
        result = (value - 1) & 0xFF
        self._zero_flag = not result
        self._negative_flag = bool(result & 0x80)
        return result

    def _cmp(self, first, addr):
        """
        Compare two values and sets the flags accordingly.

        :param int first: First value to compare.
        :param int second: Second value to compare.
        """
        second = self._read_byte(addr)
        self._zero_flag = first == second
        self._carry_flag = second <= first
        self._negative_flag = bool((first - second) & 0x80)

    def _adc(self, addr):
        """
        Add the accumulator to the passed in value using the carry flag and update the accumulator.

        :param int value: Value to add.
        """
        value = self._read_byte(addr)
        result = value + self._accumulator + int(self._carry_flag)
        signed_result = (
            self._signed(value) + self._signed(self._accumulator) + int(self._carry_flag)
        )
        self._carry_flag = result > 255
        self._accumulator = result & 0xFF
        self._zero_flag = not self._accumulator
        self._overflow_flag = signed_result < -128 or signed_result > 127
        self._negative_flag = bool(result & 0x80)

    def _sbc(self, addr):
        """
        Substract the passed in value and the carry flag from the accumulator and update the
        accumulator.

        :param int value: Value to add.
        """
        value = self._read_byte(addr)
        # I gave up trying to understand this operand, so I copied code from Nintendulator.
        # https://github.com/quietust/nintendulator/blob/master/src/CPU.cpp#L805-L813
        result = self._accumulator + (value ^ 0xFF) + int(self._carry_flag)
        self._overflow_flag = bool(
            (self._accumulator ^ value) & (self._accumulator ^ result) & 0x80
        )
        self._carry_flag = bool(result & 0x100)
        self._accumulator = result & 0xFF
        self._zero_flag = self._accumulator == 0
        self._negative_flag = bool(self._accumulator & 0x80)

    def _rmw_memory(self, addr, instruction):
        """
        Read a byte from memory, operates on the retrieved byte and writes it
        back to memory.

        :param int addr: Address to read/write to.
        :param callable instruction: Method that will operate on the byte.
        """
        value = self._read_byte(addr)
        # Write the byte back to the source before executing the instruction.
        self._write_byte(addr, value)
        self._write_byte(addr, instruction(value))

    def _rmw_index_x(self, instruction):
        """
        Run an instruction on the X register and store the result in X.

        :param callable instruction: Method that will operate on the register.
        """
        self._index_x = instruction(self._index_x)
        # Waste a cycle, not documented why.
        self._tick()

    def _rmw_index_y(self, instruction):
        """
        Run an instruction on the Y register and store the result in Y.

        :param callable instruction: Method that will operate on the register.
        """
        self._index_y = instruction(self._index_y)
        # Waste a cycle, not documented why.
        self._tick()

    def _rmw_accumulator(self, instruction):
        """
        Run an instruction on the accumulator and store the result in the
        accumulator.

        :param callable instruction: Method that will operate on the register.
        """
        # RMW instructions always waste a cycle writing back the original
        # value back to the memory location. For the accumulator, we can
        # simply tick.
        self._tick()
        self._accumulator = instruction(self._accumulator)

    def _signed(self, value):
        """
        Turn an unsigned byte into a signed value.

        Values between 0 to 127 remain the value while values between
        128 and 255 get remapped to -128 to -1.

        :param value: Value to convert.
        """
        if value > 127:
            return -256 + value
        return value

    def _unknown_opcode(self, opcode):
        """
        Raises an NotImplementedError with the opcode number.

        :param int opcode: Opcode to raise the error with.
        """
        raise NotImplementedError(
            f"Unknown opcode {hex(opcode)} at {hex(self._program_counter - 1)}"
        )
