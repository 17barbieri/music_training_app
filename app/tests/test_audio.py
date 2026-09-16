import numpy as np
import pytest

from app.audio.sine_player import SineWavePlayer


def test_a4_frequency():
    player = SineWavePlayer()

    frequency = player.midi_to_frequency(69)

    assert np.isclose(
        frequency,
        440.0,
        atol=1e-6,
    )


def test_c4_frequency():
    player = SineWavePlayer()

    frequency = player.midi_to_frequency(60)

    assert np.isclose(
        frequency,
        261.625565,
        atol=1e-3,
    )


def test_tone_generation():
    player = SineWavePlayer()

    signal = player.generate_tone(
        midi_note=60,
        duration=1.0,
    )

    assert signal.dtype == np.float32

    assert len(signal) == (
        player.SAMPLE_RATE
    )


def test_chord_generation():
    player = SineWavePlayer()

    signal = player.generate_chord(
        [60, 64, 67],
        duration=1.0,
    )

    assert signal.dtype == np.float32

    assert len(signal) == (
        player.SAMPLE_RATE
    )

    assert np.max(
        np.abs(signal)
    ) <= 1.0


def test_tone_outside_playable_range_raises_error():
    player = SineWavePlayer()

    with pytest.raises(ValueError):
        player.generate_tone(35)


def test_chord_outside_playable_range_raises_error():
    player = SineWavePlayer()

    with pytest.raises(ValueError):
        player.generate_chord([60, 97])