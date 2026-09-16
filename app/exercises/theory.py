from __future__ import annotations


INTERVALS: dict[str, int] = {
    "Unison": 0,
    "Minor 2nd": 1,
    "Major 2nd": 2,
    "Minor 3rd": 3,
    "Major 3rd": 4,
    "Perfect 4th": 5,
    "Tritone": 6,
    "Perfect 5th": 7,
    "Minor 6th": 8,
    "Major 6th": 9,
    "Minor 7th": 10,
    "Major 7th": 11,
    "Octave": 12,
}


# Reverse lookup:
#
#     INTERVAL_NAMES[4] -> "Major 3rd"
#
# This is useful when evaluating an exercise whose answer is stored
# internally as a number of semitones.
INTERVAL_NAMES: dict[int, str] = {
    semitones: name
    for name, semitones in INTERVALS.items()
}


# Initial difficulty definitions.
#
# These are deliberately simple for the first prototype.
# The difficulty system can later become much more sophisticated and
# account for melodic/harmonic presentation, direction, register,
# consonance, tonal context, etc.
INTERVAL_DIFFICULTIES: dict[str, list[int]] = {
    "Beginner": [
        0,
        7,
        12,
    ],
    "Intermediate": [
        3,
        4,
        5,
        7,
        8,
        9,
    ],
    "Advanced": list(range(13)),
}


CHORDS: dict[str, list[int]] = {
    "Major": [0, 4, 7],
    "Minor": [0, 3, 7],
    "Diminished": [0, 3, 6],
    "Augmented": [0, 4, 8],
    "Major 7th": [0, 4, 7, 11],
    "Minor 7th": [0, 3, 7, 10],
    "Dominant 7th": [0, 4, 7, 10],
    "Half-diminished 7th": [0, 3, 6, 10],
    "Diminished 7th": [0, 3, 6, 9],
}


PROGRESSIONS: list[str] = [
    "I – IV – V",
    "I – V – I",
    "ii – V – I",
    "I – V – vi – IV",
    "I – vi – IV – V",
]