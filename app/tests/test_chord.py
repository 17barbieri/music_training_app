import pytest

from app.exercises.chord import ChordExercise
from app.exercises.chord_generator import ChordGenerator


def test_chord_answer_includes_quality_and_inversion():
    exercise = ChordExercise(60, "Major", 1, (64, 67, 72))

    assert exercise.answer == "Major - 1st inversion"
    assert exercise.is_correct("Major - 1st inversion")


def test_generator_creates_all_inversion_positions():
    generator = ChordGenerator(min_note=56, max_note=76)
    positions = {
        generator.generate(["Major"]).inversion
        for _ in range(100)
    }

    assert positions == {0, 1, 2}


def test_generator_supports_seventh_chord_inversions():
    exercise = ChordGenerator(min_note=56, max_note=76).generate(
        ["Dominant 7th"]
    )

    assert len(exercise.notes) == 4
    assert exercise.answer in {
        "Dominant 7th - Root position",
        "Dominant 7th - 1st inversion",
        "Dominant 7th - 2nd inversion",
        "Dominant 7th - 3rd inversion",
    }


def test_generator_rejects_empty_or_unknown_chords():
    generator = ChordGenerator()

    with pytest.raises(ValueError):
        generator.generate([])

    with pytest.raises(ValueError):
        generator.generate(["Unknown"])