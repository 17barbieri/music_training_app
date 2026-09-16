from __future__ import annotations

import json
from pathlib import Path


class ConfusionMatrix:
    """Persist answer confusions grouped by exercise type."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".harmony_trainer" / "confusion_matrix.json"
        self._data: dict[str, dict[str, dict[str, int]]] = {}
        self._load()

    def record(
        self,
        exercise_type: str,
        expected: str,
        given: str,
    ) -> None:
        exercise = self._data.setdefault(exercise_type, {})
        expected_answers = exercise.setdefault(expected, {})
        expected_answers[given] = expected_answers.get(given, 0) + 1
        self._save()

    def get(self, exercise_type: str) -> dict[str, dict[str, int]]:
        return {
            expected: dict(given_answers)
            for expected, given_answers in self._data.get(exercise_type, {}).items()
        }

    def reset(self, exercise_type: str) -> None:
        self._data.pop(exercise_type, None)
        self._save()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = {}

        if isinstance(loaded, dict):
            self._data = loaded

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._data, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError:
            pass
