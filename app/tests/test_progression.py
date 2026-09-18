from app.exercises.progression import ProgressionExercise
from app.exercises.progression_generator import ProgressionGenerator


def test_progression_generator_creates_diatonic_sequence_in_range():
    exercise = ProgressionGenerator(
        min_note=56,
        max_note=76,
        min_length=3,
        max_length=7,
    ).generate()

    assert 3 <= len(exercise.degrees) <= 7
    assert exercise.degrees[0] == "I"
    assert len(exercise.degrees) == len(exercise.chords)
    assert all(56 <= note <= 76 for chord in exercise.chords for note in chord)
    assert set(exercise.degrees) <= {"I", "ii", "iii", "IV", "V", "vi", "vii"}


def test_progression_reveals_and_checks_prefixes():
    exercise = ProgressionExercise(
        ("I", "V", "vi"),
        ((60, 64, 67), (67, 71, 74), (69, 72, 76)),
    )

    assert exercise.is_correct_at(0, "I")
    assert not exercise.is_correct_at(1, "ii")
    assert exercise.revealed_answer(2) == "I - V"
    assert exercise.answer == "I - V - vi"


def test_cadence_targets_are_guaranteed():
    generator = ProgressionGenerator(seed=11)

    assert generator.generate("perfect_authentic").degrees[-2:] == ("V", "I")
    assert generator.generate("plagal").degrees[-2:] == ("IV", "I")
    assert generator.generate("deceptive").degrees[-2:] == ("V", "vi")
    assert generator.generate("half").degrees[-1:] == ("V",)


def test_seed_reproduces_harmonic_sequence_and_voicing():
    first = ProgressionGenerator(seed=42).generate()
    second = ProgressionGenerator(seed=42).generate()

    assert first == second
    assert len(first.degrees) == len(first.chords) == len(first.inversions)
    assert len(first.functions) == len(first.degrees)