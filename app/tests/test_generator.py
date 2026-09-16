import pytest

from app.exercises.generator import IntervalGenerator


def test_generator_returns_allowed_interval():
    generator = IntervalGenerator()

    allowed_intervals = [3, 4, 7]

    exercise = generator.generate(
        allowed_intervals
    )

    assert (
        exercise.interval_semitones
        in allowed_intervals
    )


def test_generated_second_note_is_inside_range():
    generator = IntervalGenerator(
        min_note=48,
        max_note=72,
    )

    for _ in range(100):
        exercise = generator.generate(
            [3, 4, 7, 12]
        )

        assert exercise.root_note >= 48
        assert exercise.second_note <= 72


def test_empty_interval_list_raises_error():
    generator = IntervalGenerator()

    with pytest.raises(ValueError):
        generator.generate([])


def test_negative_interval_raises_error():
    generator = IntervalGenerator()

    with pytest.raises(ValueError):
        generator.generate([-1])


def test_interval_above_octave_raises_error():
    generator = IntervalGenerator()

    with pytest.raises(ValueError):
        generator.generate([13])


def test_invalid_note_range_raises_error():
    with pytest.raises(ValueError):
        IntervalGenerator(
            min_note=72,
            max_note=48,
        )


def test_generator_rejects_notes_outside_playable_range():
    with pytest.raises(ValueError):
        IntervalGenerator(min_note=35)

    with pytest.raises(ValueError):
        IntervalGenerator(max_note=97)


def test_range_too_small_for_interval():
    generator = IntervalGenerator(
        min_note=60,
        max_note=60,
    )

    with pytest.raises(ValueError):
        generator.generate([12])