# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.

from emnes.gamepad import Gamepad

import pytest


@pytest.mark.parametrize(
    "button_name,button_index",
    [
        ("a", 0),
        ("b", 1),
        ("select", 2),
        ("start", 3),
        ("up", 4),
        ("down", 5),
        ("left", 6),
        ("right", 7),
    ],
)
def test_buttons(button_name, button_index):
    """
    Test button presses one at a time to see if the
    right bit gets set.
    """
    g = Gamepad()
    setattr(g, button_name, True)

    # Causes a refresh of the button.
    g.write(1)
    g.write(0)

    # Makes sure all the buttons before the selected have not
    # been trigger.
    for i in range(0, button_index):
        assert g.read() == 0

    # Make sure the tested button got triggered.
    assert g.read() == 1

    # Make sure the buttons after haven't.
    for i in range(button_index + 1, 7):
        assert g.read() == 0
