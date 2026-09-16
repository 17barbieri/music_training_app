# Harmony Trainer

A compact Python desktop prototype for music theory, ear-training and harmony exercises.

This repository contains a small, self-contained prototype focused on programmatic audio (sine waves), an exercise generator, and a simple Qt-based UI. It's intended for experimentation and as a foundation for larger teaching tools.

## Quick overview

- Minimal desktop app using PySide6 for the UI.
- Programmatic sine-wave audio in `app/audio/sine_player.py`.
- Exercise generation in `app/exercises/` (intervals, chords, progressions).
- Tests in `app/tests/` covering core audio and theory utilities.

## Requirements

- Python 3.11 or 3.12 recommended.
- See `requirements.txt` and `requirements-dev.txt` for exact packages.

Core runtime dependencies (examples):

- PySide6
- NumPy

Development/test dependencies:

- pytest
- pytest-qt

## Installation (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the app

From the project root run:

```bash
python -m app.main
```

Running as a module ensures package imports resolve correctly.

## Run tests

```bash
pytest -q
```

## Project layout

```
app/
    __init__.py
    main.py                # application entry point
    audio/
        sine_player.py       # simple sine-wave audio backend
    exercises/
        generator.py         # exercise creation logic
        interval.py
        theory.py            # music-theory definitions
    ui/
        main_window.py       # Qt main window
tests/
    test_audio.py
    test_generator.py
    test_interval.py
    test_theory.py
```

## What changed in this README

- Rewritten for clarity and concise developer onboarding.
- Added explicit quick start, run, and test commands.

## Notes & next steps

- The audio engine is intentionally simple (sine synthesis); replaceable later.
- If you'd like, I can: run the test suite now, add contributing notes, or expand developer setup.

---
Generated: concise README for developer onboarding and quick tests.
Augmented
```

Then:

```text
Major 7th
Minor 7th
Dominant 7th
Half-diminished 7th
Diminished 7th
```

Later:

* inversions
* open/closed voicings
* omitted notes
* extended chords
* altered chords

## Harmonic progression recognition

Initial progressions:

```text
I – IV – V
I – V – I
ii – V – I
I – V – vi – IV
I – vi – IV – V
```

Later:

* cadence recognition
* minor-key progressions
* secondary dominants
* borrowed chords
* modulation
* chromatic harmony

## Planned scoring system

The first scoring system will be deliberately simple:

```text
Correct answer   → +1
Incorrect answer → +0
```

Later, statistics can include:

```text
Accuracy
Response time
Streak
Difficulty
Exercise category
```

## Adaptive training

A future version should avoid selecting exercises uniformly.

For example:

```text
Major 3rd       91%
Minor 3rd       88%
Perfect 4th     76%
Perfect 5th     84%
Tritone         43%
```

The application could increase the frequency of weak categories.

Eventually, a confusion matrix could be used to identify specific confusions between musical intervals or chord qualities.

## Development principles

### 1. Keep audio independent

The exercise engine should never contain code such as:

```python
play_mp3("C4.mp3")
```

Instead:

```python
audio.play_note(60)
```

This allows the audio implementation to change later.

### 2. Represent music structurally

Prefer:

```python
{
    "root": 60,
    "quality": "major",
}
```

over hard-coded note names.

### 3. Keep UI logic separate

The UI should display exercises and collect answers.

It should not contain the implementation of music theory.

### 4. Make exercise generation deterministic when useful

A random generator should eventually accept a seed so that exercises can be reproduced during testing.

### 5. Test music theory independently from the GUI

For example:

```python
assert INTERVALS["Major 3rd"] == 4
```

should not require launching the graphical application.

## Next implementation milestone

The next milestone should implement a complete **interval-recognition exercise loop**:

```text
Select "Interval recognition"
             ↓
Generate random root note
             ↓
Generate random interval
             ↓
Generate corresponding MIDI notes
             ↓
Play the notes
             ↓
User selects answer
             ↓
Evaluate
             ↓
Display:
    Correct / Incorrect
             ↓
Update score
             ↓
Next exercise
```

Only after this works reliably should chord recognition and progression recognition be added.

## Future piano implementation

Once the exercise architecture is validated, the sine-wave backend can be replaced by a more realistic piano system.

Potential approaches include:

* SoundFont + FluidSynth
* piano sample library
* dedicated software synthesizer
* MIDI output to an external instrument

The rest of the application should ideally remain unchanged.
