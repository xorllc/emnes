# emnes

## Introduction

Why another NES emulator? There are so many after all? Why not help a team working on an existing one? Well, I have a couple of reasons why I want to write one myself from scratch.

- Most emulators are written in C++. I've already written a Gameboy Emulator in C++ and I want to try my hand at writing optimized Python code.
- I believe documentation is one of the most important skill for a developer and I want to get better at it. So I want to craft a documentation that is easy to read and publish.
- But most importantly, I'm doing this for fun.

# Running the emulator

1. Clone the repo
2. From the root of the repo, type `python -m emnes <path-to-a-rom>`. Launching the emulator without a rom will display a list of options.

Here's are the command line options:

```
EmNES emulator.

Usage:
    python -m emnes <path-to-rom> [--no-vsync | --no-rendering] [--nb-seconds=<n>] [--no-jit-warmup]

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

The controllers are hardcoded. Port 1 has a gamepad and port 2 has a zapper.

Here are the keyboard mapping for the gamepad:

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

If you have a Xbox One-like controller connected, you can use it to control the gamepad. The mappings are

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


## Documentation

Visit this [page](docs/README.md) to learn how the emulator works internally.
