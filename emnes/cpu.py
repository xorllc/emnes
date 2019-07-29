# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

# from emnes.instructions import instructions


class CPU:
    """
    Brain of the emulator. You can call emulate to execute an instruction.

    The CPU communicates via the various devices through the :class:`MemoryBus`.
    """

    __slots__ = [
        # These are the CPU registers
        "_accumulator",
        "_index_x",
        "_index_y",
        "_program_counter",
        "_stack_pointer",
        # These are the individuals bits of the status register.
        "_carry_flag",
        "_zero_flag",
        "_interrupt_disabled_flag",
        # This flag is implemented, but the NES CPU doesn't support decimal mode
        "_decimal_mode_flag",
        "_overflow_flag",
        "_negative_flag",
        "_memory_bus",
        "_opcodes",
    ]

    def __init__(self, memory_bus):
        """
        :param emnes.MemoryBus memory_bus: Bus the CPU will use to read and write memory.
        """
        self._memory_bus = memory_bus

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

        self.reset()

        # Allocate room for all the opcodes.
        # Prefill the array with unknown opcodes functors. We'll them replace them
        # with real instructions. This is better than inserting Nones in the array
        # and testing for them each emulation cycle. It saves a lot of time. Like 1 second on a 3
        # seconds run in PyPy
        self._opcodes = list(lambda: self._unknown_opcode(i) for i in range(256))

        # NOP
        self._opcodes[0xEA] = lambda: None

        # Break
        self._opcodes[0x00] = self._break

        ############################################################################################
        # Status register modifiers
        self._opcodes[0x78] = lambda: self._set_interupt_disable_flag(True)
        self._opcodes[0x58] = lambda: self._set_interupt_disable_flag(False)
        self._opcodes[0xF8] = lambda: self._set_decimal_mode_flag(True)
        self._opcodes[0xD8] = lambda: self._set_decimal_mode_flag(False)
        self._opcodes[0x18] = lambda: self._set_carry_flag(False)
        self._opcodes[0x38] = lambda: self._set_carry_flag(True)
        self._opcodes[0xB8] = lambda: self._set_overflow_flag(False)

        ############################################################################################
        # Stack related operations
        self._opcodes[0x28] = self._pop_status_register
        self._opcodes[0x08] = self._push_status_register
        self._opcodes[0x48] = lambda: self._push_byte(self._accumulator)
        self._opcodes[0x68] = lambda: self._load_accumulator(self._pop_byte())

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
        self._opcodes[0x84] = lambda: self._memory_bus.write_byte(self._zero_page(), self._index_y)
        self._opcodes[0x94] = lambda: self._memory_bus.write_byte(
            self._zero_page_x(), self._index_y
        )
        self._opcodes[0x8C] = lambda: self._memory_bus.write_byte(self._absolute(), self._index_y)

        # X -> Memory
        self._opcodes[0x86] = lambda: self._memory_bus.write_byte(self._zero_page(), self._index_x)
        self._opcodes[0x96] = lambda: self._memory_bus.write_byte(
            self._zero_page_y(), self._index_x
        )
        self._opcodes[0x8E] = lambda: self._memory_bus.write_byte(self._absolute(), self._index_x)

        # Accumulator -> Memory
        self._opcodes[0x85] = lambda: self._memory_bus.write_byte(
            self._zero_page(), self._accumulator
        )
        self._opcodes[0x95] = lambda: self._memory_bus.write_byte(
            self._zero_page_x(), self._accumulator
        )
        self._opcodes[0x8D] = lambda: self._memory_bus.write_byte(
            self._absolute(), self._accumulator
        )
        self._opcodes[0x9D] = lambda: self._memory_bus.write_byte(
            self._absolute_x(), self._accumulator
        )
        self._opcodes[0x99] = lambda: self._memory_bus.write_byte(
            self._absolute_y(), self._accumulator
        )
        self._opcodes[0x81] = lambda: self._memory_bus.write_byte(
            self._indirect_x(), self._accumulator
        )
        self._opcodes[0x91] = lambda: self._memory_bus.write_byte(
            self._indirect_y(), self._accumulator
        )

        ############################################################################################
        # Loads opcodes
        # Accumulator <- X|Y|Memory
        self._opcodes[0x98] = lambda: self._load_accumulator(self._index_y)
        self._opcodes[0x8A] = lambda: self._load_accumulator(self._index_x)
        self._opcodes[0xA9] = lambda: self._load_accumulator(self._immediate_read())
        self._opcodes[0xA5] = lambda: self._load_accumulator(self._zero_page_read())
        self._opcodes[0xB5] = lambda: self._load_accumulator(self._zero_page_x_read())
        self._opcodes[0xAD] = lambda: self._load_accumulator(self._absolute_read())
        self._opcodes[0xBD] = lambda: self._load_accumulator(self._absolute_x_read())
        self._opcodes[0xB9] = lambda: self._load_accumulator(self._absolute_y_read())
        self._opcodes[0xA1] = lambda: self._load_accumulator(self._indirect_x_read())
        self._opcodes[0xB1] = lambda: self._load_accumulator(self._indirect_y_read())

        # Y <- Memory|Accumulator
        self._opcodes[0xA0] = lambda: self._load_index_y(self._immediate_read())
        self._opcodes[0xA4] = lambda: self._load_index_y(self._zero_page_read())
        self._opcodes[0xB4] = lambda: self._load_index_y(self._zero_page_x_read())
        self._opcodes[0xAC] = lambda: self._load_index_y(self._absolute_read())
        self._opcodes[0xBC] = lambda: self._load_index_y(self._absolute_x_read())
        self._opcodes[0xA8] = lambda: self._load_index_y(self._accumulator)

        # X <- Memory|Accumulator|Stack Pointer
        self._opcodes[0xA2] = lambda: self._load_index_x(self._immediate_read())
        self._opcodes[0xA6] = lambda: self._load_index_x(self._zero_page_read())
        self._opcodes[0xB6] = lambda: self._load_index_x(self._zero_page_y_read())
        self._opcodes[0xAE] = lambda: self._load_index_x(self._absolute_read())
        self._opcodes[0xBE] = lambda: self._load_index_x(self._absolute_y_read())
        self._opcodes[0xAA] = lambda: self._load_index_x(self._accumulator)
        self._opcodes[0xBA] = lambda: self._load_index_x(self._stack_pointer)

        # SP <- X
        self._opcodes[0x9A] = self._transfer_index_x_to_stack_pointer

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
        self._opcodes[0x24] = lambda: self._bit(self._zero_page_read())
        self._opcodes[0x2C] = lambda: self._bit(self._absolute_read())

        # Shift left
        self._opcodes[0x0A] = lambda: self._rmw_accumulator(self._asl)
        self._opcodes[0x06] = lambda: self._rmw_memory(self._zero_page(), self._asl)
        self._opcodes[0x16] = lambda: self._rmw_memory(self._zero_page_x(), self._asl)
        self._opcodes[0x0E] = lambda: self._rmw_memory(self._absolute(), self._asl)
        self._opcodes[0x1E] = lambda: self._rmw_memory(self._absolute_x(), self._asl)

        # Shift right
        self._opcodes[0x4A] = lambda: self._rmw_accumulator(self._logical_shift_right)
        self._opcodes[0x46] = lambda: self._rmw_memory(self._zero_page(), self._logical_shift_right)
        self._opcodes[0x56] = lambda: self._rmw_memory(
            self._zero_page_x(), self._logical_shift_right
        )
        self._opcodes[0x4E] = lambda: self._rmw_memory(self._absolute(), self._logical_shift_right)
        self._opcodes[0x5E] = lambda: self._rmw_memory(
            self._absolute_x(), self._logical_shift_right
        )

        # Rotate left
        self._opcodes[0x2A] = lambda: self._rmw_accumulator(self._rotate_left)
        self._opcodes[0x26] = lambda: self._rmw_memory(self._zero_page(), self._rotate_left)
        self._opcodes[0x36] = lambda: self._rmw_memory(self._zero_page_x(), self._rotate_left)
        self._opcodes[0x2E] = lambda: self._rmw_memory(self._absolute(), self._rotate_left)
        self._opcodes[0x3E] = lambda: self._rmw_memory(self._absolute_x(), self._rotate_left)

        # Rotate Right
        self._opcodes[0x6A] = lambda: self._rmw_accumulator(self._rotate_right)
        self._opcodes[0x66] = lambda: self._rmw_memory(self._zero_page(), self._rotate_right)
        self._opcodes[0x76] = lambda: self._rmw_memory(self._zero_page_x(), self._rotate_right)
        self._opcodes[0x6E] = lambda: self._rmw_memory(self._absolute(), self._rotate_right)
        self._opcodes[0x7E] = lambda: self._rmw_memory(self._absolute_x(), self._rotate_right)

        # OR
        self._opcodes[0x09] = lambda: self._logical_inclusive_or(self._immediate_read())
        self._opcodes[0x05] = lambda: self._logical_inclusive_or(self._zero_page_read())
        self._opcodes[0x15] = lambda: self._logical_inclusive_or(self._zero_page_x_read())
        self._opcodes[0x0D] = lambda: self._logical_inclusive_or(self._absolute_read())
        self._opcodes[0x1D] = lambda: self._logical_inclusive_or(self._absolute_x_read())
        self._opcodes[0x19] = lambda: self._logical_inclusive_or(self._absolute_y_read())
        self._opcodes[0x01] = lambda: self._logical_inclusive_or(self._indirect_x_read())
        self._opcodes[0x11] = lambda: self._logical_inclusive_or(self._indirect_y_read())

        # Exclusive OR
        self._opcodes[0x49] = lambda: self._exclusive_or(self._immediate_read())
        self._opcodes[0x45] = lambda: self._exclusive_or(self._zero_page_read())
        self._opcodes[0x55] = lambda: self._exclusive_or(self._zero_page_x_read())
        self._opcodes[0x4D] = lambda: self._exclusive_or(self._absolute_read())
        self._opcodes[0x5D] = lambda: self._exclusive_or(self._absolute_x_read())
        self._opcodes[0x59] = lambda: self._exclusive_or(self._absolute_y_read())
        self._opcodes[0x41] = lambda: self._exclusive_or(self._indirect_x_read())
        self._opcodes[0x51] = lambda: self._exclusive_or(self._indirect_y_read())

        # AND
        self._opcodes[0x29] = lambda: self._logical_and(self._immediate_read())
        self._opcodes[0x25] = lambda: self._logical_and(self._zero_page_read())
        self._opcodes[0x35] = lambda: self._logical_and(self._zero_page_x_read())
        self._opcodes[0x2D] = lambda: self._logical_and(self._absolute_read())
        self._opcodes[0x3D] = lambda: self._logical_and(self._absolute_x_read())
        self._opcodes[0x39] = lambda: self._logical_and(self._absolute_y_read())
        self._opcodes[0x21] = lambda: self._logical_and(self._indirect_x_read())
        self._opcodes[0x31] = lambda: self._logical_and(self._indirect_y_read())

        ############################################################################################
        # Arithmetic
        # Increment
        self._opcodes[0xE6] = lambda: self._rmw_memory(self._zero_page(), self._increment)
        self._opcodes[0xF6] = lambda: self._rmw_memory(self._zero_page_x(), self._increment)
        self._opcodes[0xEE] = lambda: self._rmw_memory(self._absolute(), self._increment)
        self._opcodes[0xFE] = lambda: self._rmw_memory(self._absolute_x(), self._increment)
        self._opcodes[0xE8] = lambda: self._rmw_index_x(self._increment)
        self._opcodes[0xC8] = lambda: self._rmw_index_y(self._increment)

        # Decrement
        self._opcodes[0xCA] = lambda: self._rmw_index_x(self._decrement)
        self._opcodes[0x88] = lambda: self._rmw_index_y(self._decrement)
        self._opcodes[0xC6] = lambda: self._rmw_memory(self._zero_page(), self._decrement)
        self._opcodes[0xD6] = lambda: self._rmw_memory(self._zero_page_x(), self._decrement)
        self._opcodes[0xCE] = lambda: self._rmw_memory(self._absolute(), self._decrement)
        self._opcodes[0xDE] = lambda: self._rmw_memory(self._absolute_x(), self._decrement)

        # Compare
        self._opcodes[0xE0] = lambda: self._compare(self._index_x, self._immediate_read())
        self._opcodes[0xE4] = lambda: self._compare(self._index_x, self._zero_page_read())
        self._opcodes[0xEC] = lambda: self._compare(self._index_x, self._absolute_read())
        self._opcodes[0xC0] = lambda: self._compare(self._index_y, self._immediate_read())
        self._opcodes[0xC4] = lambda: self._compare(self._index_y, self._zero_page_read())
        self._opcodes[0xCC] = lambda: self._compare(self._index_y, self._absolute_read())
        self._opcodes[0xC9] = lambda: self._compare(self._accumulator, self._immediate_read())
        self._opcodes[0xC5] = lambda: self._compare(self._accumulator, self._zero_page_read())
        self._opcodes[0xD5] = lambda: self._compare(self._accumulator, self._zero_page_x_read())
        self._opcodes[0xCD] = lambda: self._compare(self._accumulator, self._absolute_read())
        self._opcodes[0xDD] = lambda: self._compare(self._accumulator, self._absolute_x_read())
        self._opcodes[0xD9] = lambda: self._compare(self._accumulator, self._absolute_y_read())
        self._opcodes[0xC1] = lambda: self._compare(self._accumulator, self._indirect_x_read())
        self._opcodes[0xD1] = lambda: self._compare(self._accumulator, self._indirect_y_read())

        # Add
        self._opcodes[0x69] = lambda: self._add_with_carry(self._immediate_read())
        self._opcodes[0x65] = lambda: self._add_with_carry(self._zero_page_read())
        self._opcodes[0x75] = lambda: self._add_with_carry(self._zero_page_x_read())
        self._opcodes[0x6D] = lambda: self._add_with_carry(self._absolute_read())
        self._opcodes[0x7D] = lambda: self._add_with_carry(self._absolute_x_read())
        self._opcodes[0x79] = lambda: self._add_with_carry(self._absolute_y_read())
        self._opcodes[0x61] = lambda: self._add_with_carry(self._indirect_x_read())
        self._opcodes[0x71] = lambda: self._add_with_carry(self._indirect_y_read())

        # Substract
        self._opcodes[0xE9] = lambda: self._substract_with_carry(self._immediate_read())
        self._opcodes[0xE5] = lambda: self._substract_with_carry(self._zero_page_read())
        self._opcodes[0xF5] = lambda: self._substract_with_carry(self._zero_page_x_read())
        self._opcodes[0xED] = lambda: self._substract_with_carry(self._absolute_read())
        self._opcodes[0xFD] = lambda: self._substract_with_carry(self._absolute_x_read())
        self._opcodes[0xF9] = lambda: self._substract_with_carry(self._absolute_y_read())
        self._opcodes[0xE1] = lambda: self._substract_with_carry(self._indirect_x_read())
        self._opcodes[0xF1] = lambda: self._substract_with_carry(self._indirect_y_read())

    def emulate(self):
        """
        Emulate one instruction.
        """
        self._opcodes[self._read_code_byte()]()

    ################################################################################################
    # Accessors for the registers

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
        self._stack_pointer = (self._stack_pointer - 3) & 0xFF
        self._program_counter = self._memory_bus.read_word(0xFFFC)

    def _read_code_byte(self):
        """
        Fetch one byte and moves the program counter forward by one byte.

        :returns: The byte that was read.
        :rtype: int
        """
        byte = self._memory_bus.read_byte(self._program_counter)
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
        word = self._memory_bus.read_word(self._program_counter)
        self._program_counter += 2
        return word

    ############################################################################
    # The following methods compute the address referred by the operand.

    # _zero_page would simply pass-through to _read_core_byte, so alias the
    # method name so we save one function call, which are expensive.
    _zero_page = _read_code_byte

    def _zero_page_x(self):
        """
        Compute a memory address by adding the value of the next byte + X.

        :returns: Address between 0 and 255.
        """
        return (self._zero_page() + self._index_x) & 0xFF

    def _zero_page_y(self):
        """
        Compute a memory address by adding the value of the next byte + Y.

        :returns: Address between 0 and 255.
        """
        return (self._zero_page() + self._index_y) & 0xFF

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
        return self._memory_bus.read_byte(first_addr) | (
            self._memory_bus.read_byte(second_addr) << 8
        )

    def _absolute_x(self):
        """
        Compute memory address taken from the next word + index x.

        :returns: Address between 0 and 65535.
        """
        return (self._absolute() + self._index_x) & 0xFFFF

    def _absolute_y(self):
        """
        Compute memory address taken from the next word + index y.

        :returns: Address between 0 and 65535.
        """
        return (self._absolute() + self._index_y) & 0xFFFF

    def _indirect(self):
        """
        Compute memory address taken at the address referred by the next word.

        :returns: Address between 0 and 65535.
        """
        return self._memory_bus.read_word(self._absolute())

    def _indirect_x(self):
        """
        Retrieve address in memory found at the zero page x address.

        :returns: Address between 0 and 65535.
        """
        addr = self._zero_page_x()
        return self._memory_bus.read_byte(addr) | (
            self._memory_bus.read_byte((addr + 1) & 0xFF) << 8
        )

    def _indirect_y(self):
        """
        Retrieve address in memory found at the zero page address and
        adds the y offset.

        :returns: Address between 0 and 65535.
        """
        addr = self._zero_page()
        return (
            (
                self._memory_bus.read_byte(addr)
                | (self._memory_bus.read_byte((addr + 1) & 0xFF) << 8)
            )
            + self._index_y
        ) & 0xFFFF

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
    # The following methods retrieve the value referenced by the address of the
    # operand.

    _immediate_read = _read_code_byte

    def _zero_page_read(self):
        """
        Read memory at zero page address.

        :returns: A byte.
        """
        return self._memory_bus.read_byte(self._zero_page())

    def _zero_page_x_read(self):
        """
        Read memory at zero page x address.

        :returns: A byte.
        """
        return self._memory_bus.read_byte(self._zero_page_x())

    def _zero_page_y_read(self):
        """
        Read memory at zero page y address.

        :returns: A byte.
        """
        return self._memory_bus.read_byte(self._zero_page_y())

    def _absolute_read(self):
        """
        Read memory at abslute address.

        :returns: A byte.
        """
        return self._memory_bus.read_byte(self._absolute())

    def _absolute_x_read(self):
        """
        Read memory at absolute x address.

        :returns: A byte.
        """
        return self._memory_bus.read_byte(self._absolute_x())

    def _absolute_y_read(self):
        """
        Read memory at absolute y address.

        :returns: A byte.
        """
        return self._memory_bus.read_byte(self._absolute_y())

    def _indirect_x_read(self):
        """
        Read memory at indirect x address.

        :returns: A byte.
        """
        return self._memory_bus.read_byte(self._indirect_x())

    def _indirect_y_read(self):
        """
        Read memory at indirect y address.

        :returns: A byte.
        """
        return self._memory_bus.read_byte(self._indirect_y())

    ############################################################################
    # The following methods operate on the stack.

    def _push_byte(self, value):
        """
        Push a byte on the stack.

        :param int value: Value to push on the stack.
        """
        self._memory_bus.write_byte((self._stack_pointer + 0x100), value)
        self._stack_pointer = (self._stack_pointer - 1) & 0xFF

    def _pop_byte(self):
        """
        Pop a byte from the stack.

        :returns: A byte.
        """
        self._stack_pointer = (self._stack_pointer + 1) & 0xFF
        return self._memory_bus.read_byte(self._stack_pointer + 0x100)

    def _push_word(self, value):
        """
        Push a word on the stack.

        :param int value: Value to push on the stack.
        """
        self._push_byte(value >> 8)
        self._push_byte(value & 0xFF)

    def _pop_word(self):
        """
        Pop a word from the stack.

        :returns: A byte.
        """
        return self._pop_byte() | (self._pop_byte() << 8)

    ############################################################################
    # The following emulates the CPU opcodes

    def _break(self):
        """
        Save the current program counter and status register and jump to the
        interrupt handler address read from 0xFEEE
        """
        self._push_word(self._program_counter + 1)
        self._push_status_register()
        addr = self._memory_bus.read_word(0xFFFE)
        self._program_counter = addr
        self._interrupt_disabled_flag = True
        
    def _set_interupt_disable_flag(self, value):
        """
        Set the interrupt disable flag.

        :param bool value: Value to set the flag.
        """
        self._interrupt_disabled_flag = value

    def _set_carry_flag(self, value):
        """
        Set the carry flag.

        :param bool value: Value to set the flag.
        """
        self._carry_flag = value

    def _set_overflow_flag(self, value):
        """
        Set the overflow flag.

        :param bool value: Value to set the flag.
        """
        self._overflow_flag = value

    def _set_decimal_mode_flag(self, value):
        """
        Set the decimal mode flag.

        :param bool value: Value to set the flag.
        """
        self._decimal_mode_flag = value
        
    def _pop_status_register(self):
        """
        Pop the status register from the stack.
        """
        value = self._pop_byte()
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
        self._push_byte(self.status | 0b00010000)
        
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
        jump_to = self._absolute()
        self._push_word(self._program_counter - 1)
        self._program_counter = jump_to

    def _jump_from_subroutine(self):
        """
        Jump to the memory location at the top of the stack.
        """
        self._program_counter = self._pop_word() + 1

    def _return_from_interrupt(self):
        """
        Pop the status register and program counter from the stack.
        """
        self._pop_status_register()
        self._program_counter = self._pop_word()

    def _load_index_x(self, value):
        """
        Load value into register x.
        """
        self._index_x = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)
        
    def _load_index_y(self, value):
        """
        Load value into register y.

        :param int value: Value to load.
        """
        self._index_y = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)

    def _load_accumulator(self, value):
        """
        Load value into accumulator

        :param int value: Value to load.
        """
        self._accumulator = value
        self._zero_flag = not value
        self._negative_flag = bool(value & 0x80)
        
    def _transfer_index_x_to_stack_pointer(self):
        """
        Load X into stack pointer.
        """
        self._stack_pointer = self._index_x
        
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
            self._program_counter += offset
            
    def _bit(self, value):
        """
        Test the overflow and negative bit and zero value of the passed in value.

        :param int value: Value to test.
        """
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

    def _logical_inclusive_or(self, value):
        """
        Update the accumulator with the result of accumulator | value

        :param int value: Value to or with.
        """
        self._accumulator = self._accumulator | value
        self._zero_flag = not self._accumulator
        self._negative_flag = bool(self._accumulator & 0x80)

    def _exclusive_or(self, value):
        """
        Update the accumulator with the result of accumulator ^ value

        :param int value: Value to exclusive or with.
        """
        self._accumulator = self._accumulator ^ value
        self._zero_flag = not self._accumulator
        self._negative_flag = bool(self._accumulator & 0x80)

    def _logical_and(self, value):
        """
        Update the accumulator with the result of accumulator & value

        :param int value: Value to and with.
        """
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

    def _compare(self, first, second):
        """
        Compare two values and sets the flags accordingly.

        :param int first: First value to compare.
        :param int second: Second value to compare.
        """
        self._zero_flag = first == second
        self._carry_flag = second <= first
        self._negative_flag = bool((first - second) & 0x80)

    def _add_with_carry(self, value):
        """
        Add the accumulator to the passed in value using the carry flag and update the accumulator.

        :param int value: Value to add.
        """
        result = value + self._accumulator + int(self._carry_flag)
        signed_result = (
            self._signed(value) + self._signed(self._accumulator) + int(self._carry_flag)
        )
        self._carry_flag = result > 255
        self._accumulator = result & 0xFF
        self._zero_flag = not self._accumulator
        self._overflow_flag = signed_result < -128 or signed_result > 127
        self._negative_flag = bool(result & 0x80)

    def _substract_with_carry(self, value):
        """
        Substract the passed in value and the carry flag from the accumulator and update the
        accumulator.

        :param int value: Value to add.
        """
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
        value = self._memory_bus.read_byte(addr)
        self._memory_bus.write_byte(addr, instruction(value))

    def _rmw_index_x(self, instruction):
        """
        Run an instruction on the X register and store the result in X.

        :param callable instruction: Method that will operate on the register.
        """
        self._index_x = instruction(self._index_x)

    def _rmw_index_y(self, instruction):
        """
        Run an instruction on the Y register and store the result in Y.

        :param callable instruction: Method that will operate on the register.
        """
        self._index_y = instruction(self._index_y)

    def _rmw_accumulator(self, instruction):
        """
        Run an instruction on the accumulator and store the result in the
        accumulator.

        :param callable instruction: Method that will operate on the register.
        """
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
        raise NotImplementedError(f"Unknown opcode {hex(opcode)}")
