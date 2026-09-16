import json

from app.exercises.confusion_matrix import ConfusionMatrix


def test_matrix_is_created_and_persisted(tmp_path):
    path = tmp_path / "confusion-matrix.json"
    matrix = ConfusionMatrix(path)

    assert path.exists()
    matrix.record("Interval recognition", "Major 3rd", "Minor 3rd")
    matrix.record("Interval recognition", "Major 3rd", "Minor 3rd")

    reloaded = ConfusionMatrix(path)
    assert reloaded.get("Interval recognition") == {
        "Major 3rd": {"Minor 3rd": 2},
    }


def test_matrix_reset_is_scoped_to_exercise(tmp_path):
    path = tmp_path / "confusion-matrix.json"
    matrix = ConfusionMatrix(path)
    matrix.record("Interval recognition", "Major 3rd", "Minor 3rd")
    matrix.record("Chord recognition", "Major", "Minor")

    matrix.reset("Interval recognition")

    assert matrix.get("Interval recognition") == {}
    assert matrix.get("Chord recognition") == {"Major": {"Minor": 1}}
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "Chord recognition": {"Major": {"Minor": 1}},
    }