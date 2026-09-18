from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressionExercise:
    """Represent a diatonic chord-progression identification exercise."""

    degrees: tuple[str, ...]
    chords: tuple[tuple[int, ...], ...]
    functions: tuple[str, ...] = ()
    inversions: tuple[int, ...] = ()
    cadence: str | None = None
    tonic_pc: int = 0

    @property
    def answer(self) -> str:
        return " - ".join(self.degrees)

    def is_correct_at(self, index: int, answer: str) -> bool:
        return self.degrees[index] == answer

    def revealed_answer(self, count: int) -> str:
        return " - ".join(self.degrees[:count])
