# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name="emnes",
    version="0.1.0",
    description="Nintendo emulator.",
    author="Jean-François Boismenu",
    url="https://github.com/jfboismenu/emnes",
    # Recursively discover all packages in python folder, excluding any tests
    packages=find_packages("python"),
    # Everything can be found under the python folder, but installed without it
    package_dir={"": "python"},
    install_requires=["docopt", "pysdl2"],
    entry_points={"console_scripts": ["emnes = emnes.main:main"]},
)
