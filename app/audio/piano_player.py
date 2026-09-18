from __future__ import annotations

import ctypes
import os
import sys
import time
from pathlib import Path

from app.config import HIGHEST_PLAYABLE_NOTE, LOWEST_PLAYABLE_NOTE


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOUNDFONT = PROJECT_ROOT / "assets" / "piano.sf3"
NATIVE_AUDIO_DIRECTORY = PROJECT_ROOT / "native"
INSTALLED_NATIVE_AUDIO_DIRECTORIES = [
    Path.home() / "Applications" / "FluidSynth" / "bin",
]


class PianoPlayer:
    """Play MIDI notes through FluidSynth and a piano SoundFont."""

    def __init__(
        self,
        soundfont_path: Path = DEFAULT_SOUNDFONT,
        lowest_note: int = LOWEST_PLAYABLE_NOTE,
        highest_note: int = HIGHEST_PLAYABLE_NOTE,
    ) -> None:
        if lowest_note > highest_note:
            raise ValueError(
                "lowest_note must be less than or equal to highest_note."
            )
        if lowest_note < 0 or highest_note > 127:
            raise ValueError("MIDI notes must be between 0 and 127.")
        if not soundfont_path.exists():
            raise FileNotFoundError(
                f"Piano SoundFont was not found: {soundfont_path}"
            )

        self.lowest_note = lowest_note
        self.highest_note = highest_note
        self.soundfont_path = soundfont_path
        self._dll_directory_handles = []
        self._load_native_library()

        import fluidsynth

        self.synth = fluidsynth.Synth(samplerate=44_100)
        if sys.platform == "win32":
            self.synth.start(driver="dsound", midi_driver="winmidi")
        else:
            self.synth.start()

        soundfont_id = self.synth.sfload(str(soundfont_path))
        if soundfont_id < 0:
            self.close()
            raise RuntimeError(f"Could not load SoundFont: {soundfont_path}")
        self.synth.program_select(0, soundfont_id, 0, 0)

    def _load_native_library(self) -> None:
        """Make the repository's FluidSynth DLL discoverable on Windows."""

        if sys.platform == "win32":
            directories = [NATIVE_AUDIO_DIRECTORY]
            directories.extend(INSTALLED_NATIVE_AUDIO_DIRECTORIES)
            available_directories = [
                directory for directory in directories if directory.exists()
            ]
            os.environ["PATH"] = (
                os.pathsep.join(str(directory) for directory in available_directories)
                + os.pathsep
                + os.environ.get("PATH", "")
            )

            for directory in available_directories:
                self._dll_directory_handles.append(
                    os.add_dll_directory(str(directory))
                )

            dll_names = ("libfluidsynth.dll", "libfluidsynth-3.dll")
            for directory in available_directories:
                for dll_name in dll_names:
                    dll_path = directory / dll_name
                    if not dll_path.exists():
                        continue
                    try:
                        ctypes.CDLL(str(dll_path))
                        return
                    except OSError:
                        continue

            raise OSError(
                "Could not load FluidSynth. Include its dependent DLLs "
                "next to libfluidsynth.dll or install FluidSynth in "
                f"{INSTALLED_NATIVE_AUDIO_DIRECTORIES[0]}."
            )

    def _validate_note(self, midi_note: int) -> None:
        if not self.lowest_note <= midi_note <= self.highest_note:
            raise ValueError(
                f"MIDI note {midi_note} is outside the playable range "
                f"({self.lowest_note}-{self.highest_note})."
            )

    def play_note(
        self,
        midi_note: int,
        velocity: int = 100,
        duration: float = 0.7,
    ) -> None:
        self._validate_note(midi_note)
        self.synth.noteon(0, midi_note, velocity)
        time.sleep(duration)
        self.synth.noteoff(0, midi_note)

    def play_chord(
        self,
        midi_notes: list[int],
        velocity: int = 100,
        duration: float = 1.0,
    ) -> None:
        if not midi_notes:
            raise ValueError("A chord must contain at least one note.")
        for midi_note in midi_notes:
            self._validate_note(midi_note)

        for midi_note in midi_notes:
            self.synth.noteon(0, midi_note, velocity)

        time.sleep(duration)

        for midi_note in midi_notes:
            self.synth.noteoff(0, midi_note)

    def close(self) -> None:
        if getattr(self, "synth", None) is not None:
            self.synth.delete()
            self.synth = None
        for handle in self._dll_directory_handles:
            handle.close()
        self._dll_directory_handles.clear()