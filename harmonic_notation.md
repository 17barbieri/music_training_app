# Harmonic Progression Notation

Progression questions generate notation through `app/exercises/notation.py`.

## Generation flow

1. `ProgressionGenerator` creates the harmonic sequence and MIDI voicings.
2. The tonic pitch class is stored on `ProgressionExercise` as `tonic_pc`.
3. `LilyPondRenderer` converts the MIDI voicings to LilyPond chord literals.
4. The renderer writes a temporary `progression.ly` file.
5. It runs the discovered `lilypond.exe` with the SVG backend.
6. The UI displays the resulting SVG in a separate **Progression notation** window.

The `.ly` source and SVG are generated when the progression question is created, not only when the user presses the notation button. The temporary directory is deleted when the next question is generated or the application closes.

## LilyPond content

Each generated file contains:

- a major key signature derived from the `I` chord tonic;
- `4/4` meter;
- one simultaneous chord per quarter-note beat;
- the Roman numerals below the staff using LilyPond lyrics.

The tonic pitch class determines a standard major-key spelling. For example, a tonic pitch class of `8` produces `\\key aes \\major` and uses flat spellings such as `aes` and `des`. Sharp keys use spellings such as `fis`, `cis`, and `gis`.

## Executable discovery

LilyPond is located in this order:

1. `LILYPOND_EXECUTABLE`, when set;
2. `lilypond.exe` or `lilypond` in the current process `PATH`;
3. the persisted user installation pattern `~/Applications/lilypond-*/bin/lilypond.exe`.

If no executable is found, progression generation still works. The notation button displays an explanatory error instead of preventing other exercises from starting.

## UI behavior

The **View notation** button is visible only for the harmonic progression exercise. It opens the rendered SVG in a new dialog and leaves the exercise window available underneath. Rendering errors are shown in a warning dialog.
