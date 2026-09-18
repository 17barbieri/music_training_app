from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import tempfile

from app.exercises.progression import ProgressionExercise


KEYS = {
    0: ("c", "c", ["c", "d", "e", "f", "g", "a", "b"]),
    1: ("des", "des", ["des", "ees", "f", "ges", "aes", "bes", "c"]),
    2: ("d", "d", ["d", "e", "fis", "g", "a", "b", "cis"]),
    3: ("ees", "ees", ["ees", "f", "g", "aes", "bes", "c", "d"]),
    4: ("e", "e", ["e", "fis", "gis", "a", "b", "cis", "dis"]),
    5: ("f", "f", ["f", "g", "a", "bes", "c", "d", "e"]),
    6: ("fis", "fis", ["fis", "gis", "ais", "b", "cis", "dis", "eis"]),
    7: ("g", "g", ["g", "a", "b", "c", "d", "e", "fis"]),
    8: ("aes", "aes", ["aes", "bes", "c", "des", "ees", "f", "g"]),
    9: ("a", "a", ["a", "b", "cis", "d", "e", "fis", "gis"]),
    10: ("bes", "bes", ["bes", "c", "d", "ees", "f", "g", "a"]),
    11: ("b", "b", ["b", "cis", "dis", "e", "fis", "gis", "ais"]),
}


class LilyPondRenderer:
    """Create a LilyPond SVG for a progression exercise."""

    def __init__(self, lilypond_executable: Path | None = None) -> None:
        self.lilypond_executable = lilypond_executable or self._find_lilypond()

    @staticmethod
    def _find_lilypond() -> Path:
        candidates: list[Path] = []
        configured = os.environ.get("LILYPOND_EXECUTABLE")
        if configured:
            candidates.append(Path(configured))
        for entry in os.environ.get("PATH", "").split(os.pathsep):
            candidates.append(Path(entry) / "lilypond.exe")
            candidates.append(Path(entry) / "lilypond")
        if os.name == "nt":
            try:
                import winreg

                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                ) as key:
                    user_path, _ = winreg.QueryValueEx(key, "Path")
                for entry in user_path.split(os.pathsep):
                    candidates.append(Path(entry) / "lilypond.exe")
            except (OSError, FileNotFoundError):
                pass
        candidates.extend(Path.home().glob("Applications/lilypond-*/bin/lilypond.exe"))
        resolved = shutil.which("lilypond.exe") or shutil.which("lilypond")
        if resolved:
            candidates.insert(0, Path(resolved))
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(
            "lilypond.exe was not found. Add its bin directory to PATH or "
            "set LILYPOND_EXECUTABLE."
        )

    @staticmethod
    def _pitch_name(midi_note: int, tonic_pc: int) -> str:
        key_name, _, scale_names = KEYS[tonic_pc]
        scale_pcs = [(tonic_pc + offset) % 12 for offset in (0, 2, 4, 5, 7, 9, 11)]
        pitch_name = scale_names[scale_pcs.index(midi_note % 12)]
        octave = midi_note // 12 - 1
        marker = "'" * max(0, octave - 3) + "," * max(0, 3 - octave)
        return f"{pitch_name}{marker}"

    def source_for(self, exercise: ProgressionExercise) -> str:
        tonic_pc = exercise.tonic_pc
        key_name, _, _ = KEYS[tonic_pc]
        chords = " ".join(
            f"<{ ' '.join(self._pitch_name(note, tonic_pc) for note in chord) }>4"
            for chord in exercise.chords
        )
        numerals = " ".join(exercise.degrees)
        return f'''\\version "2.24.0"
\\header {{
  title = "Harmonic Progression"
  subtitle = "{key_name.capitalize()} major"
}}
\\score {{
  <<
    \\new Staff <<
      \\new Voice = "progression" {{
        \\clef treble
        \\key {key_name} \\major
        \\time 4/4
        {chords}
      }}
      \\new Lyrics \\lyricsto "progression" {{ {numerals} }}
    >>
  >>
  \\layout {{ }}
}}
'''

    def render(self, exercise: ProgressionExercise) -> tuple[Path, tempfile.TemporaryDirectory[str]]:
        temporary_directory = tempfile.TemporaryDirectory(prefix="harmony-trainer-")
        directory = Path(temporary_directory.name)
        source_path = directory / "progression.ly"
        source_path.write_text(self.source_for(exercise), encoding="utf-8")
        result = subprocess.run(
            [str(self.lilypond_executable), "-dbackend=svg", "-o", str(directory / "progression"), str(source_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        svg_path = directory / "progression.svg"
        if result.returncode != 0 or not svg_path.exists():
            temporary_directory.cleanup()
            raise RuntimeError(
                "LilyPond could not render the progression.\n"
                f"{result.stderr or result.stdout}"
            )
        return svg_path, temporary_directory
