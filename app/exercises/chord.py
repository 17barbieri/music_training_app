from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChordExercise:
    """Represent one chord-identification exercise."""

    root_note: int
    chord_name: str
    inversion: int
    notes: tuple[int, ...]

    @property
    def answer(self) -> str:
        positions = [
            "Root position",
            "1st inversion",
            "2nd inversion",
            "3rd inversion",
        ]
        position = positions[self.inversion]
        return f"{self.chord_name} - {position}"

    def is_correct(self, answer: str) -> bool:
        return answer == self.answer
