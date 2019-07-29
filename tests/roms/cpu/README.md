# Blargg

Contains a suite of tests that test each opcode individually and fully, with all exceptions.
The official_only.nes tests only official instructions. all_instrs.nes is keep, but will
most likely never be implemented. Stripped were roms for individual tests and source code.

# nestest

This is a simple test, great for writing an emulator. It contains a expectation file that
allows to know the processor state before executing each instruction, allowing your
test to validate the complete state. Note that unsupported opcodes are tested towards the end
which our test will not test.
