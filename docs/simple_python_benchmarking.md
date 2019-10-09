# Simple Python Benchmarking

First, we have to determine if Python is even able to run loops fast enough for emulating the NES. Unfortunately, the news aren't so good for CPython. I want to avoid using C++ in a Python module, so we'll have to get creative or using versions of CPython that run on another VM, like [Pyijon](https://github.com/microsoft/Pyjion). The that produced these results can be found [here](https://github.com/jfboismenu/pynes/blob/master/dev/benchmark_looping.py).

## 13" Macbook Pro, 2017

| Interpreter  | Time                |
| ------------ | ------------------- |
| Python 3.6.4 | 1.27 seconds        |
| PyPy 3.6.7   | 0.014 seconds       |

## iPhone 7 Plus

| Interpreter      | Time                |
| ---------------- | ------------------- |
| Pythonista 3.6.1 | 1.14 seconds        |

## iPad, 6th Gen

| Interpreter      | Time                |
| ---------------- | ------------------- |
| Pythonista 3.6.1 | 1.15 seconds        |
