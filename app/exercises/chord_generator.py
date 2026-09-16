from __future__ import annotations

import random

from app.config import HIGHEST_PLAYABLE_NOTE, LOWEST_PLAYABLE_NOTE
from app.exercises.chord import ChordExercise
from app.exercises.theory import CHORDS


class ChordGenerator:
    """Generate random chord-identification exercises."""

    def __init__(
        self,
        min_note: int = LOWEST_PLAYABLE_NOTE,
        max_note: int = HIGHEST_PLAYABLE_NOTE,
    ) -> None:
        if min_note > max_note:
            raise ValueError("min_note must be less than or equal to max_note.")
        if min_note < LOWEST_PLAYABLE_NOTE:
            raise ValueError("min_note is below the lowest playable note.")
        if max_note > HIGHEST_PLAYABLE_NOTE:
            raise ValueError("max_note is above the highest playable note.")
        self.min_note = min_note
        self.max_note = max_note

    def generate(self, allowed_chords: list[str]) -> ChordExercise:
        if not allowed_chords:
            raise ValueError("allowed_chords must not be empty.")
        if any(chord not in CHORDS for chord in allowed_chords):
            raise ValueError("allowed_chords contains an unknown chord.")

        chord_name = random.choice(allowed_chords)
        intervals = CHORDS[chord_name]
        inversion = 0 if chord_name == "Augmented" else random.randrange(len(intervals))
        inverted_intervals = (
            intervals[inversion:]
            + [interval + 12 for interval in intervals[:inversion]]
        )
        highest_offset = max(inverted_intervals)
        maximum_root = self.max_note - highest_offset
        if self.min_note > maximum_root:
            raise ValueError("Note range is too small for the requested chord.")

        root_note = random.randint(self.min_note, maximum_root)
        notes = tuple(root_note + interval for interval in inverted_intervals)
        return ChordExercise(root_note, chord_name, inversion, notes)
