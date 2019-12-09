# emnes

## Introduction

Why another NES emulator? There are so many after all? Why not help a team working on an existing one? Well, there's a couple reason why this once needed to exist.

- Most emulators are written in C++. I've already written a Gameboy Emulator in C++ and my weapon of choice right now is Python.
- Documentation is one of the most important skill for a developer, so the goal of this emulator is to document as much as possible the process of emulating a console.
- But most importantly: fun.

## Disclaimer

This emulator was written for learning, not to play games I do not own. As such, all the games used during development have a physical counterpart in my collection. Please do not pirate games, even 30+ year old ones.

# Running the emulator

The emulator requires PyPy. The standard Python implementation is way too slow to emulate the NES. This emulator runs about 60 times faster (3fps vs 180fps) in certain scenarios. You can install PyPy3 via `pyenv` on macOS.

Then,

1. Clone the repository.
2. From inside the repository, type `pip install .`.
2. Type `emnes <path-to-rom>` to launch the emulator.

or

1. Type `pip install git+https://github.com/jfboismenu/emnes.git#egg=emnes`.
2. Type `emnes <path-to-rom>` from anywhere.

Here are the command line options:

```
EmNES emulator.

Usage:
    emnes <path-to-rom> [--no-vsync | --no-rendering] [--nb-seconds=<n>] [--no-jit-warmup]

Options:
    -h --help           Show this screen
    --no-rendering      Runs the emulator without rendering anything on the screen.
    --no-vsync          Disables VSync. Emulator runs as fast as possible.
    --nb-seconds=<n>    Runs the emulation for n seconds (in emulator time) and quits.
                        This is useful for benchmarking.
    --no-jit-warmup     Disables JIT warmup (PyPy only). Faster game startup but poorer performance
                        up front.
```

# Controllers

The controllers are hard-coded. Port 1 has a game pad and port 2 has a zapper.

Here are the keyboard mapping for the game pad:

| NES    | PC    |
|--------|-------|
| Up     | Up    |
| Down   | Down  |
| Left   | Left  |
| Right  | Right |
| A      | X     |
| B      | Z     |
| Start  | S     |
| Select | A     |

If you have a Xbox One-like controller connected, you can use it to control the game pad. The mappings are

| NES    | Gamepad    |
|--------|------------|
| Up     | Up         |
| Down   | Down       |
| Left   | Left       |
| Right  | Right      |
| A      | A or B     |
| B      | X or Y     |
| Start  | Hamburger  |
| Select | 2-squares  |

The zapper is controlled with the mouse. Aim with the cursor and trigger with the left mouse button.

You can toggle on/off audio channels via the keys 1 to 5.

1: Toggle pulse channel 1
2: Toggle pulse channel 2
3: Toggle triangle channel
4: Toggle noise channel
5: Toggle DMC channel

## Documentation

Visit this [page](docs/README.md) to learn about this emulator.
