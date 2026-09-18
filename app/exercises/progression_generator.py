from __future__ import annotations

from dataclasses import dataclass
import random

from app.config import HIGHEST_PLAYABLE_NOTE, LOWEST_PLAYABLE_NOTE
from app.exercises.progression import ProgressionExercise


HARMONIC_FUNCTIONS = {
    "I": "TONIC", "vi": "TONIC", "iii": "TONIC",
    "ii": "PREDOMINANT", "IV": "PREDOMINANT",
    "V": "DOMINANT", "vii": "DOMINANT",
}
SCALE_ROOTS = {"I": 0, "ii": 2, "iii": 4, "IV": 5, "V": 7, "vi": 9, "vii": 11}
TEMPLATES = (
    ("I", "IV", "V", "I"),
    ("I", "ii", "V", "I"),
    ("vi", "ii", "V", "I"),
    ("iii", "vi", "ii", "V", "I"),
    ("IV", "I"), ("V", "I"), ("V", "vi"),
    ("I", "IV", "V"), ("I", "V", "vi", "IV"),
)
CADENCE_TAILS = {
    "perfect_authentic": ("V", "I"),
    "imperfect_authentic": ("V", "I"),
    "plagal": ("IV", "I"),
    "half": ("V",),
    "deceptive": ("V", "vi"),
}
CHORD_INTERVALS = {
    "I": (0, 4, 7), "ii": (0, 3, 7), "iii": (0, 3, 7),
    "IV": (0, 4, 7), "V": (0, 4, 7), "vi": (0, 3, 7),
    "vii": (0, 3, 6),
}


@dataclass(frozen=True)
class HarmonicDifficulty:
    min_length: int = 3
    max_length: int = 7
    max_chord_types: int = 7
    allow_sevenths: bool = False
    inversion_probabilities: tuple[float, float, float] = (0.60, 0.30, 0.10)
    cadence_complexity: int = 1
    allow_secondary_dominants: bool = False
    voice_leading_complexity: int = 1


class ProgressionGenerator:
    """Generate grammar-first, validated diatonic progressions."""

    def __init__(
        self,
        min_note: int = LOWEST_PLAYABLE_NOTE,
        max_note: int = HIGHEST_PLAYABLE_NOTE,
        difficulty: HarmonicDifficulty | None = None,
        seed: int | None = None,
        classical_voice_leading: bool = False,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        if min_note > max_note or min_note < LOWEST_PLAYABLE_NOTE or max_note > HIGHEST_PLAYABLE_NOTE:
            raise ValueError("Progression notes must stay within the playable range.")
        self.min_note, self.max_note = min_note, max_note
        base_difficulty = difficulty or HarmonicDifficulty()
        if min_length is not None or max_length is not None:
            self.difficulty = HarmonicDifficulty(
                min_length=(
                    min_length
                    if min_length is not None
                    else base_difficulty.min_length
                ),
                max_length=(
                    max_length
                    if max_length is not None
                    else base_difficulty.max_length
                ),
                max_chord_types=base_difficulty.max_chord_types,
                allow_sevenths=base_difficulty.allow_sevenths,
                inversion_probabilities=base_difficulty.inversion_probabilities,
                cadence_complexity=base_difficulty.cadence_complexity,
                allow_secondary_dominants=base_difficulty.allow_secondary_dominants,
                voice_leading_complexity=base_difficulty.voice_leading_complexity,
            )
        else:
            self.difficulty = base_difficulty
        if self.difficulty.min_length < 3 or self.difficulty.max_length > 7:
            raise ValueError("Progression lengths must be between 3 and 7.")
        self.random = random.Random(seed)
        self.classical_voice_leading = classical_voice_leading

    def _harmonic_sequence(self, cadence: str | None) -> tuple[str, ...]:
        length = self.random.randint(self.difficulty.min_length, self.difficulty.max_length)
        if cadence:
            if cadence not in CADENCE_TAILS:
                raise ValueError(f"Unsupported cadence: {cadence}")
            tail = CADENCE_TAILS[cadence]
            if len(tail) > length:
                raise ValueError("Cadence does not fit progression length.")
            prefix_length = length - len(tail)
            prefix = ("I",) if prefix_length else ()
            while len(prefix) < prefix_length:
                prefix += (self.random.choice(("I", "vi", "iii", "ii", "IV", "V")),)
            return prefix[:prefix_length] + tail
        template = self.random.choice(tuple(t for t in TEMPLATES if len(t) <= length))
        sequence = list(template)
        while len(sequence) < length:
            sequence.insert(-1, self.random.choice(("ii", "IV", "V")))
        return tuple(sequence)

    def _voicing(self, degrees: tuple[str, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
        inversions: list[int] = []
        chords: list[tuple[int, ...]] = []
        previous: tuple[int, ...] | None = None
        for index, degree in enumerate(degrees):
            intervals = CHORD_INTERVALS[degree]
            if self.difficulty.allow_sevenths and degree in ("I", "ii", "V") and self.random.random() < 0.35:
                intervals = intervals + ((11,) if degree == "I" else (10,))
            if (
                index + 1 < len(degrees)
                and index > 0
                and degrees[index - 1:index + 2] == ("I", "V", "I")
            ):
                inversion = 2 if len(intervals) == 3 and degree == "V" else 0
            else:
                inversion = self.random.choices(range(min(3, len(intervals))), weights=self.difficulty.inversion_probabilities[:min(3, len(intervals))])[0]
            ordered = intervals[inversion:] + tuple(i + 12 for i in intervals[:inversion])
            root = self.min_note + SCALE_ROOTS[degree]
            if previous:
                candidates = []
                for octave in range(-2, 4):
                    candidate = tuple(note + 12 * octave for note in ordered)
                    if min(candidate) >= self.min_note and max(candidate) <= self.max_note and all(abs(a - b) <= 12 for a, b in zip(candidate, previous[:len(candidate)])):
                        candidates.append(candidate)
                chord = min(candidates, key=lambda c: sum(abs(a - b) for a, b in zip(c, previous[:len(c)]))) if candidates else tuple(root + note for note in ordered)
            else:
                chord = tuple(root + note for note in ordered)
            chords.append(chord)
            inversions.append(inversion)
            previous = chord
        return tuple(chords), tuple(inversions)

    def _validate(self, degrees: tuple[str, ...], chords: tuple[tuple[int, ...], ...]) -> None:
        if len(degrees) < 3 or len(degrees) > 7 or degrees[0] != "I":
            raise ValueError("Invalid progression structure.")
        if any(degree not in HARMONIC_FUNCTIONS for degree in degrees):
            raise ValueError("Unknown harmonic function.")
        if any(tuple(sorted(chord)) != chord for chord in chords):
            raise ValueError("Voice crossing detected.")
        if any(note < self.min_note or note > self.max_note for chord in chords for note in chord):
            raise ValueError("Voicing exceeds configured range.")
        if self.classical_voice_leading:
            for left, right in zip(chords, chords[1:]):
                if any(abs(a - b) > 12 for a, b in zip(left, right)):
                    raise ValueError("Excessive voice movement.")

    def generate(self, cadence: str | None = None) -> ProgressionExercise:
        for _ in range(20):
            degrees = self._harmonic_sequence(cadence)
            chords, inversions = self._voicing(degrees)
            try:
                self._validate(degrees, chords)
            except ValueError:
                continue
            return ProgressionExercise(
                degrees,
                chords,
                tuple(HARMONIC_FUNCTIONS[d] for d in degrees),
                inversions,
                cadence,
                self.min_note % 12,
            )
        raise RuntimeError("Unable to generate a valid harmonic progression.")
