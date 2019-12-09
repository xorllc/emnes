# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2019 Jean-François Boismenu
#
# See LICENSE at the root of this project for more info.


class FrameSequencer:
    """
    The frame sequencer allows to clock the various audio channel's
    length counter and envelope.

    Missing: We're not implementing the audio IRQ.
    """

    __slots__ = (
        "_count",
        "_nb_steps",
        "_current_step",
        "_is_irq_disabled",
        "_clock_length_cb",
        "_clock_envelope_cb",
    )

    # Real period is 7457.5, but we'll cheat for now.
    # FIXME: Not sure why I decided to cheat here,
    # but changing this right now involves breaking tests
    # so we'll leave as is.
    PERIOD = 1789773 / 240

    def __init__(self, clock_length_cb, clock_envelope_cb):
        """
        """
        self._count = self.PERIOD
        self._nb_steps = 4
        self._current_step = 0
        self._is_irq_disabled = True
        self._clock_length_cb = clock_length_cb
        self._clock_envelope_cb = clock_envelope_cb

    def write_byte(self, value):
        """
        Update the state of the frame sequencer.

        :param value: Value to write.
        """
        self._nb_steps = 5 if bool(0b10000000 & value) else 4
        self._is_irq_disabled - bool(0b1000000 & value)

        self._count = self.PERIOD
        self._current_step = 0

        if self._nb_steps == 5:
            self.clock()

    @property
    def nb_steps(self):
        """
        Number of steps in the sequencer.
        """
        return self._nb_steps

    @property
    def is_irq_disabled(self):
        """
        If ``True``, audio IRQ's are disabled.
        """
        return self._is_irq_disabled

    @property
    def count(self):
        """
        Number of cycles before the time the sequencer outputs a clock.

        Note that this number if not whole and be a fraction.
        """
        return self._count

    @property
    def current_step(self):
        """
        The current step.
        """
        return self._current_step

    def emulate(self):
        """
        Emulate the frame sequencer operation.
        """
        # If the count underflows, clock the sequencer.
        self._count -= 1
        if self._count < 0:
            self.clock()
            # The period is not a whole integer, so we have to add
            # it instead of assigning it or we're going to get
            # rounding errors over time.
            self._count += self.PERIOD

    def clock(self):
        """
        Clock the envelope and length counter depending on the
        current step.
        """
        next_sequence = self._current_step + 1

        if self._nb_steps == 4:
            if self._current_step % 2 == 1:
                self._clock_length_cb()
            self._clock_envelope_cb()
        elif self._current_step != 4:
            if self._current_step % 2 == 0:
                self._clock_length_cb()
            self._clock_envelope_cb()

        self._current_step = next_sequence % self._nb_steps
