# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


from unittest import mock
from emnes.apu.frame_sequencer import FrameSequencer


def test_initial_state():
    f = FrameSequencer(mock.Mock(), mock.Mock())
    assert f.count == 1789773 / 240
    assert f.nb_steps == 4
    assert f.is_irq_disabled
    assert f.current_step == 0


def test_set_5_step():
    f = FrameSequencer(mock.Mock(), mock.Mock())
    f.write_byte(0b10000000)
    assert f.nb_steps == 5
    assert f.current_step == 1


def test_set_4_step():
    f = FrameSequencer(mock.Mock(), mock.Mock())
    f.write_byte(0b00000000)
    assert f.nb_steps == 4
    assert f.current_step == 0


def test_clock_240hz():
    with mock.patch.object(FrameSequencer, "clock") as mock_clock:
        f = FrameSequencer(mock.Mock(), mock.Mock())
        assert f.nb_steps == 4
        for i in range(int(1789773 / 240 * 240) - 1):
            f.emulate()
        assert mock_clock.call_count == 239, f"Count is {f.count}."
        f.emulate()
        assert mock_clock.call_count == 240, f"Count is {f.count}."

    # With a 5 step sequencer, the sequencer gets clocked as soon
    # as you select 5 step.
    with mock.patch.object(FrameSequencer, "clock") as mock_clock:
        f = FrameSequencer(mock.Mock(), mock.Mock())
        f.write_byte(0b10000000)
        assert f.nb_steps == 5
        assert mock_clock.call_count == 1
        for i in range(1789772):
            f.emulate()
        assert mock_clock.call_count == 240
        f.emulate()
        assert mock_clock.call_count == 241


def test_clock_4_step():
    f = FrameSequencer(mock.Mock(), mock.Mock())
    f.current_step == 0
    f.clock()
    f.current_step == 1
    f.clock()
    f.current_step == 2
    f.clock()
    f.current_step == 3
    f.clock()
    f.current_step == 0


def test_clock_5_step():
    f = FrameSequencer(mock.Mock(), mock.Mock())
    f.write_byte(0b10000000)
    f.current_step == 1
    f.clock()
    f.current_step == 2
    f.clock()
    f.current_step == 3
    f.clock()
    f.current_step == 4
    f.clock()
    f.current_step == 0
    f.clock()
    f.current_step == 1


def test_clock_pulses_4_step():
    clock_envelope_callback = mock.Mock()
    clock_length_callback = mock.Mock()
    f = FrameSequencer(clock_length_callback, clock_envelope_callback)
    f.clock()
    assert clock_length_callback.call_count == 0
    assert clock_envelope_callback.call_count == 1
    f.clock()
    assert clock_length_callback.call_count == 1
    assert clock_envelope_callback.call_count == 2
    f.clock()
    assert clock_length_callback.call_count == 1
    assert clock_envelope_callback.call_count == 3
    f.clock()
    assert clock_length_callback.call_count == 2
    assert clock_envelope_callback.call_count == 4
    f.clock()
    assert clock_length_callback.call_count == 2
    assert clock_envelope_callback.call_count == 5


def test_clock_pulses_5_step():
    clock_envelope_callback = mock.Mock()
    clock_length_callback = mock.Mock()
    f = FrameSequencer(clock_length_callback, clock_envelope_callback)
    f.write_byte(0b10000000)
    f.current_step == 1
    assert clock_length_callback.call_count == 1
    assert clock_envelope_callback.call_count == 1
    f.clock()
    assert clock_length_callback.call_count == 1
    assert clock_envelope_callback.call_count == 2
    f.clock()
    assert clock_length_callback.call_count == 2
    assert clock_envelope_callback.call_count == 3
    f.clock()
    assert clock_length_callback.call_count == 2
    assert clock_envelope_callback.call_count == 4
    f.clock()
    # 5th clock is idle
    assert clock_length_callback.call_count == 2
    assert clock_envelope_callback.call_count == 4
    f.clock()
    assert clock_length_callback.call_count == 3
    assert clock_envelope_callback.call_count == 5


def test_clock_channel_fequency_4_step():
    clock_envelope_callback = mock.Mock()
    clock_length_callback = mock.Mock()
    f = FrameSequencer(clock_length_callback, clock_envelope_callback)
    for i in range(1789773):
        f.emulate()
    assert clock_length_callback.call_count == 120
    assert clock_envelope_callback.call_count == 240


def test_clock_channel_fequency_5_step():
    clock_envelope_callback = mock.Mock()
    clock_length_callback = mock.Mock()
    f = FrameSequencer(clock_length_callback, clock_envelope_callback)
    f.write_byte(0b10000000)
    f.current_step == 1
    for i in range(1789772):
        f.emulate()
    assert clock_length_callback.call_count == 96
    assert clock_envelope_callback.call_count == 192
    f.emulate()
    assert clock_length_callback.call_count == 97
    assert clock_envelope_callback.call_count == 193


def test_reset_on_write():
    f = FrameSequencer(mock.Mock(), mock.Mock())
    # Period has a remainder, so round up.
    # The emulate method does not support incrementing more than the period,
    # since we should never add more than a handful of cycles each time.
    # So call it a couple of times instead.
    for i in range(int(f.PERIOD) * 2 + 1):
        f.emulate()
    assert f.current_step == 2
    f.write_byte(0)
    assert f.count == f.PERIOD
    assert f.current_step == 0
    for i in range(int(f.PERIOD)):
        f.emulate()
    assert f.current_step == 0
    f.emulate()
    assert f.current_step == 1
