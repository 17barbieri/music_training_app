from app.exercises.notation import LilyPondRenderer
from app.exercises.progression import ProgressionExercise


def test_lilypond_source_contains_key_meter_chords_and_roman_numerals():
    exercise = ProgressionExercise(
        degrees=("I", "IV", "V", "I"),
        chords=(
            (60, 64, 67),
            (65, 69, 72),
            (67, 71, 74),
            (60, 64, 67),
        ),
        tonic_pc=0,
    )

    source = LilyPondRenderer.__new__(LilyPondRenderer).source_for(exercise)

    assert r"\key c \major" in source
    assert r"\time 4/4" in source
    assert "<c' e' g'>4" in source
    assert "I IV V I" in source


def test_lilypond_pitch_spelling_uses_flat_key_signature():
    exercise = ProgressionExercise(
        degrees=("I", "IV", "V"),
        chords=((68, 72, 75), (73, 77, 80), (75, 79, 82)),
        tonic_pc=8,
    )

    source = LilyPondRenderer.__new__(LilyPondRenderer).source_for(exercise)

    assert r"\key aes \major" in source
    assert "aes" in source
    assert "des" in source
