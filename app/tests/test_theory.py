from app.exercises.theory import (
    CHORDS,
    INTERVALS,
    PROGRESSIONS,
)


def test_major_third_is_four_semitones():
    assert INTERVALS["Major 3rd"] == 4


def test_octave_is_twelve_semitones():
    assert INTERVALS["Octave"] == 12


def test_major_chord():
    assert CHORDS["Major"] == [0, 4, 7]


def test_minor_chord():
    assert CHORDS["Minor"] == [0, 3, 7]


def test_progressions_exist():
    assert "ii – V – I" in PROGRESSIONS