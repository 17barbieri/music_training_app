# Harmonic Progression Generator

This document describes the implementation in `app/exercises/progression_generator.py`.

## Architecture

The generator has two deliberately separate stages:

1. **Harmonic grammar** chooses Roman numerals and harmonic functions.
2. **Voicing** chooses inversions and actual MIDI pitches for those numerals.

The returned `ProgressionExercise` stores both representations. The exercise can therefore be tested and displayed without depending on FluidSynth or any other audio backend.

## Harmonic grammar

The supported functions are:

| Function | Roman numerals |
| --- | --- |
| TONIC | `I`, `vi`, `iii` |
| PREDOMINANT | `ii`, `IV` |
| DOMINANT | `V`, `vii` |

The generator does not choose every chord independently. It first chooses one of the predefined templates:

- `I - IV - V - I`
- `I - ii - V - I`
- `vi - ii - V - I`
- `iii - vi - ii - V - I`
- `IV - I`
- `V - I`
- `V - vi`
- `I - IV - V`
- `I - V - vi - IV`

The requested length is between three and seven chords by default. A shorter template is extended with predominant or dominant material before its final chord, preserving a structural beginning and ending. The default sequence begins with `I`.

## Cadence targets

`ProgressionGenerator.generate(cadence=...)` supports:

- `perfect_authentic`: final `V - I`
- `imperfect_authentic`: final `V - I`, with relaxed final voicing conditions
- `plagal`: final `IV - I`
- `half`: final `V`
- `deceptive`: final `V - vi`

Cadence tails are appended after any randomized prefix. Consequently, random choices cannot invalidate the requested final cadence.

## Voicing and inversion stage

After the Roman-numeral sequence is fixed, each degree receives a diatonic triad. The generator then:

- chooses root, first, or second inversion using configurable weighted probabilities;
- keeps root position most likely by default;
- uses a cadential `I6/4 - V - I` shape when that exact context occurs;
- searches octave placements near the previous chord to minimize voice movement;
- preserves common tones where possible through the minimum-distance candidate;
- keeps pitches ordered to avoid voice crossing;
- rejects pitches outside the configured MIDI range.

The current implementation uses triads by default. `allow_sevenths=True` enables selected diatonic seventh chords for `I`, `ii`, and `V`. The `HarmonicDifficulty` object exposes this and the other training controls without coupling them to audio.

## Validation and regeneration

Every generated result is validated before it is returned. Validation checks:

- length is within the configured three-to-seven range;
- the sequence begins on `I`;
- every degree has a known harmonic function;
- every chord is ordered from low to high;
- every pitch is inside the configured range;
- classical mode rejects excessive voice movement.

If validation fails, generation retries up to twenty times. A progression that cannot satisfy the constraints raises `RuntimeError` instead of reaching the user.

## Difficulty parameters

`HarmonicDifficulty` exposes:

- `min_length`, `max_length`
- `max_chord_types`
- `allow_sevenths`
- `inversion_probabilities`
- `cadence_complexity`
- `allow_secondary_dominants`
- `voice_leading_complexity`

The first release uses the parameters that are needed by the current diatonic exercise and keeps the remaining switches available for later grammar extensions. This makes the public configuration stable while the exercise grows toward secondary dominants and more advanced voice-leading rules.

## Determinism

Pass `seed` to `ProgressionGenerator` to use a private `random.Random` instance:

```python
from app.exercises.progression_generator import ProgressionGenerator

generator = ProgressionGenerator(seed=42)
first = generator.generate()
second_run = ProgressionGenerator(seed=42).generate()
assert first == second_run
```

The seed controls template choice, prefix choices, chord qualities, inversions, and octave placement.

## Audio boundary

The generator returns MIDI tuples only. It does not import or call FluidSynth. The UI may pass those tuples to `PianoPlayer`, while tests can inspect the harmonic sequence and voicing independently.
