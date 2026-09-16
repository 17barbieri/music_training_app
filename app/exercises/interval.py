from __future__ import annotations

from dataclasses import dataclass

from app.exercises.theory import INTERVAL_NAMES


@dataclass(frozen=True)
class IntervalExercise:
    """Represent one interval-recognition exercise.

    Parameters
    ----------
    root_note:
        MIDI note number of the first note.

    interval_semitones:
        Distance between the two notes in semitones.
    """

    root_note: int
    interval_semitones: int

    @property
    def second_note(self) -> int:
        """Return the MIDI note number of the second note."""

        return self.root_note + self.interval_semitones

    @property
    def answer(self) -> str:
        """Return the human-readable name of the interval."""

        try:
            return INTERVAL_NAMES[self.interval_semitones]
        except KeyError as error:
            raise ValueError(
                f"Unsupported interval: "
                f"{self.interval_semitones} semitones."
            ) from error

    def is_correct(self, answer: str) -> bool:
        """Return whether the supplied answer is correct."""

        return answer == self.answer