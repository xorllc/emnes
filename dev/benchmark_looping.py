#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


import time

# Simple variables to do some math. Nothing fancy. We're trying to
# get an idea of the absolute floor of time we will spend spinning.
a = 0
b = 1

before = time.time()


def do_cpu(a, b):
    a += i
    b |= a
    return a, b


# We'll iterate a million times for a 1mhz CPU at the very least.
for i in range(0, int(1024 * 1024 * 1.79)):
    a, b = do_cpu(a, b)


# We'll iterate 60 times per second on a bufffer which we'll fill
# one pixel at a time in the worse case scenario.
screen_buffer = bytearray(256 * 240)


def do_screen(i):
    screen_buffer[x] = 1


for i in range(0, 60):
    for x in range(0, len(screen_buffer)):
        do_screen(i)


# We'll assume 44000hz 16-bit audio output x 5 channel for audio
audio_buffer = bytearray(44000 * 2 * 5)


def do_audio(i):
    audio_buffer[i] = 0


for i in range(0, len(audio_buffer)):
    do_audio(i)


print(f"Elapsed: {time.time() - before}")


# Results:

# 13" Macbook Pro, 2017
# ---------------------
# Python 3.6.4: 1.00 seconds
# PyPy 3.6.7: 0.012 seconds (!!!)
#
# iPhone 7 Plus
# -------------
# Pythonista 3.6.1: 1.31 seconds
#
# iPad, 6th Gen
# -------------
# Pythonista 3.6.1: 1.32 seconds
