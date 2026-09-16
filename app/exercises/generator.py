from __future__ import annotations

import random

from app.exercises.interval import IntervalExercise


class IntervalGenerator:
    """Generate random interval-recognition exercises."""

    def __init__(
        self,
        min_note: int = 48,
        max_note: int = 72,
    ) -> None:
        """Initialize the generator.

        Parameters
        ----------
        min_note:
            Lowest possible MIDI note for the root.

        max_note:
            Highest possible MIDI note for the second note.
        """

        if min_note > max_note:
            raise ValueError(
                "min_note must be less than or equal to max_note."
            )

        self.min_note = min_note
        self.max_note = max_note

    def generate(
        self,
        allowed_intervals: list[int],
    ) -> IntervalExercise:
        """Generate one random interval exercise."""

        if not allowed_intervals:
            raise ValueError(
                "allowed_intervals must not be empty."
            )

        for interval in allowed_intervals:
            if interval < 0:
                raise ValueError(
                    "Intervals must be non-negative."
                )

            if interval > 12:
                raise ValueError(
                    "Intervals greater than one octave "
                    "are not supported."
                )

        # The second note must remain inside the configured range.
        maximum_interval = max(
            allowed_intervals
        )

        maximum_root = (
            self.max_note - maximum_interval
        )

        if self.min_note > maximum_root:
            raise ValueError(
                "Note range is too small for the "
                "requested intervals."
            )

        interval = random.choice(
            allowed_intervals
        )

        # The root range must be valid for the particular
        # interval that was selected.
        maximum_root = (
            self.max_note - interval
        )

        root = random.randint(
            self.min_note,
            maximum_root,
        )

        return IntervalExercise(
            root_note=root,
            interval_semitones=interval,
        )