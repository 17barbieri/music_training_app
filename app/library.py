from __future__ import annotations

import json
from pathlib import Path


class ProgressionLibrary:
    """Persist saved and user-created harmonic progressions."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".harmony_trainer" / "library.json"
        self.entries: list[dict[str, object]] = []
        self._load()

    def add(self, degrees: list[str], source: str = "Saved exercise") -> None:
        self.entries.append({"degrees": degrees, "source": source})
        self._save()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            value = []
        if isinstance(value, list):
            self.entries = [entry for entry in value if isinstance(entry, dict)]

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.entries, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass
