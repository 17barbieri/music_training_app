from __future__ import annotations

import threading
import time

import numpy as np
from scipy.io import wavfile
from tempfile import NamedTemporaryFile
import subprocess
import sys
from pathlib import Path

from app.config import HIGHEST_PLAYABLE_NOTE, LOWEST_PLAYABLE_NOTE


class SineWavePlayer:
    """Generate and play simple sine-wave tones.

    This is intentionally a temporary audio backend for the prototype.

    Notes are represented using MIDI note numbers:
        60 = C4
        61 = C#4
        62 = D4
        etc.

    Later this class can be replaced by a real piano/synthesizer backend
    without changing the exercise or UI layers.
    """

    SAMPLE_RATE = 44_100

    def __init__(
        self,
        lowest_note: int = LOWEST_PLAYABLE_NOTE,
        highest_note: int = HIGHEST_PLAYABLE_NOTE,
    ) -> None:
        if lowest_note > highest_note:
            raise ValueError(
                "lowest_note must be less than or equal to highest_note."
            )

        if lowest_note < 0 or highest_note > 127:
            raise ValueError("MIDI notes must be between 0 and 127.")

        self.lowest_note = lowest_note
        self.highest_note = highest_note
        self._stop_event = threading.Event()

    def _validate_note(self, midi_note: int) -> None:
        if not self.lowest_note <= midi_note <= self.highest_note:
            raise ValueError(
                f"MIDI note {midi_note} is outside the playable range "
                f"({self.lowest_note}-{self.highest_note})."
            )

    @staticmethod
    def midi_to_frequency(midi_note: int) -> float:
        """Convert a MIDI note number to frequency in Hz."""
        return 440.0 * 2.0 ** ((midi_note - 69) / 12.0)

    def generate_tone(
        self,
        midi_note: int,
        duration: float = 1.0,
        amplitude: float = 0.3,
    ) -> np.ndarray:
        """Generate a sine wave for a MIDI note."""

        self._validate_note(midi_note)
        frequency = self.midi_to_frequency(midi_note)

        number_of_samples = int(self.SAMPLE_RATE * duration)
        time_axis = np.arange(number_of_samples) / self.SAMPLE_RATE

        signal = amplitude * np.sin(
            2.0 * np.pi * frequency * time_axis
        )

        return signal.astype(np.float32)

    def generate_chord(
        self,
        midi_notes: list[int],
        duration: float = 1.0,
        amplitude: float = 0.2,
    ) -> np.ndarray:
        """Generate a chord by summing several sine waves."""

        if not midi_notes:
            raise ValueError("A chord must contain at least one note.")

        for midi_note in midi_notes:
            self._validate_note(midi_note)

        signals = [
            self.generate_tone(
                midi_note,
                duration=duration,
                amplitude=amplitude,
            )
            for midi_note in midi_notes
        ]

        chord = np.sum(signals, axis=0)

        # Prevent clipping.
        maximum = np.max(np.abs(chord))
        if maximum > 0.95:
            chord = chord / maximum * 0.95

        return chord.astype(np.float32)

    def play_signal(self, signal: np.ndarray) -> None:
        """Play a generated signal.

        The first prototype uses temporary WAV files and the native
        operating-system audio player. This is deliberately simple and
        will be replaced by a proper real-time audio backend later.
        """

        self._stop_event.clear()

        signal_int16 = np.int16(
            np.clip(signal, -1.0, 1.0) * 32767
        )

        with NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as temporary_file:

            wav_path = Path(temporary_file.name)

        try:
            wavfile.write(
                wav_path,
                self.SAMPLE_RATE,
                signal_int16,
            )

            self._play_wav(wav_path)

        finally:
            if wav_path.exists():
                wav_path.unlink()

    def _play_wav(self, path: Path) -> None:
        """Play a WAV file using the platform's default audio player."""

        if sys.platform.startswith("win"):
            import winsound

            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME,
            )

        elif sys.platform == "darwin":
            subprocess.run(
                ["afplay", str(path)],
                check=False,
            )

        else:
            # Try common Linux players.
            for command in (
                ["aplay", str(path)],
                ["paplay", str(path)],
            ):
                try:
                    result = subprocess.run(
                        command,
                        check=False,
                        capture_output=True,
                    )
                    if result.returncode == 0:
                        return
                except FileNotFoundError:
                    continue

            raise RuntimeError(
                "No suitable WAV audio player was found. "
                "Install 'aplay' or 'paplay', or replace the audio backend."
            )

    def play_note(
        self,
        midi_note: int,
        duration: float = 1.0,
    ) -> None:
        """Generate and play one note."""

        signal = self.generate_tone(
            midi_note,
            duration=duration,
        )

        self.play_signal(signal)

    def play_chord(
        self,
        midi_notes: list[int],
        duration: float = 1.0,
    ) -> None:
        """Generate and play a chord."""

        signal = self.generate_chord(
            midi_notes,
            duration=duration,
        )

        self.play_signal(signal)