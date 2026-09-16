from app.exercises.interval import IntervalExercise


def test_second_note_is_correct():
    exercise = IntervalExercise(
        root_note=60,
        interval_semitones=7,
    )

    assert exercise.second_note == 67


def test_major_third_answer():
    exercise = IntervalExercise(
        root_note=60,
        interval_semitones=4,
    )

    assert exercise.answer == "Major 3rd"


def test_perfect_fifth_answer():
    exercise = IntervalExercise(
        root_note=60,
        interval_semitones=7,
    )

    assert exercise.answer == "Perfect 5th"


def test_octave_answer():
    exercise = IntervalExercise(
        root_note=60,
        interval_semitones=12,
    )

    assert exercise.answer == "Octave"


def test_correct_answer():
    exercise = IntervalExercise(
        root_note=60,
        interval_semitones=4,
    )

    assert exercise.is_correct("Major 3rd")


def test_wrong_answer():
    exercise = IntervalExercise(
        root_note=60,
        interval_semitones=4,
    )

    assert not exercise.is_correct("Perfect 5th")


def test_second_note_for_octave():
    exercise = IntervalExercise(
        root_note=60,
        interval_semitones=12,
    )

    assert exercise.second_note == 72


def test_unsupported_interval_raises_error():
    exercise = IntervalExercise(
        root_note=60,
        interval_semitones=13,
    )

    try:
        exercise.answer
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for unsupported interval."
        )