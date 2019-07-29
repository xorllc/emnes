# Setting up the development environment

To run the emulator, you need the following

## Pre-requisites

### Python 3.6+
You can download Python from [python.org](https://python.org/) for most platforms, install it with [brew](brew.sh) on macOS, install it via your favorite package manager or through the excellent [pyenv](https://github.com/pyenv/pyenv). I personnally choose `pyenv`.

### PyPy3.6
You can download PyPy from [pypy.org](https://pypy.org/) for most platforms, install it with [brew](brew.sh) on macOS, install it via your favorite package manager or through the excellent [pyenv](https://github.com/pyenv/pyenv). I personnally choose `pyenv`.

### A note about Python flavors
The code and tests works flawlessly on both flavors of Python. However, PyPy is blazingly fast, about 36 times faster than the CPython implementation.

The following were taking by running `python dev/debug_blargg.py tests/roms/cpu/blargg/official_only.nes -n 10` with both flavors:

PyPy3: Average execution time of 1.35 seconds
Python 3: 49.53

### pip
pip must be available with your interpreter. If not, download and run this [script](https://pip.pypa.io/en/stable/installing/). You might need elevated privileges to run this script if your Python is installed as part of your OS.

## Development

All code for the emulator is in the `emnes` folder.

## Documentation

All documentation is in the `docs` folder.

## Tests

Tests are written using `pytest` and can be found under `tests`.

## Code quality

All code quality verification is done via pre-commit checks. Do a `pip install pre-commit` and then type `pre-commit install` at the root of the repo.
You'll then be set up for code validation on each commit.
