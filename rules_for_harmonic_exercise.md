# HARMONIC PROGRESSION GENERATION RULES

The generator must produce musically coherent diatonic chord progressions for ear-training exercises.

1. Separate harmonic progression generation from chord voicing/inversion generation.

2. First generate a sequence of harmonic functions/Roman numerals.
   Then select chord qualities, inversions and voicings.

3. Use harmonic functions:
   - TONIC: I, vi, iii
   - PREDOMINANT: ii, IV
   - DOMINANT: V, vii°

4. Prefer functional motion:
   TONIC → PREDOMINANT → DOMINANT → TONIC.

5. Do not select chords independently with uniform probability.

6. Use predefined progression templates for common musical patterns,
   including:
   - I–IV–V–I
   - I–ii–V–I
   - vi–ii–V–I
   - iii–vi–ii–V–I
   - IV–I
   - V–I
   - V–vi
   - I–IV–V
   - I–V–vi–IV

7. Cadences must be explicit generation targets.
   Supported cadences:
   - perfect authentic: V–I
   - imperfect authentic: V–I with relaxed final conditions
   - plagal: IV–I
   - half cadence: progression ending on V
   - deceptive: V–vi

8. When an exercise targets a cadence, guarantee that its final chords
   satisfy the selected cadence. Randomness may only affect the
   preceding material.

9. Every progression must have a structural beginning and ending.
   Avoid arbitrary endings and avoid excessive repetition.

10. Inversions are generated only after the harmonic progression has
    been selected.

11. Inversions should not be uniformly random. Prefer root position,
    first inversion and contextually appropriate inversions according
    to configurable probabilities.

12. Inversions must respect harmonic context.
    In particular, cadential 6/4 should normally occur as:
        I6/4 → V → I
    rather than appearing randomly.

13. Generate actual pitches using voice-leading constraints:
    - minimize unnecessary voice movement
    - preserve common tones when possible
    - avoid excessive leaps
    - avoid voice crossing
    - respect configurable vocal/instrumental ranges

14. If classical voice-leading mode is enabled:
    - avoid parallel perfect fifths and octaves
    - resolve the leading tone toward tonic where appropriate
    - resolve chordal sevenths downward where appropriate
    - favor conventional cadential voice leading

15. The generator must validate every generated progression before
    returning it.

16. A progression that fails harmonic-function or voice-leading
    constraints must be regenerated rather than returned.

17. The generator must expose difficulty parameters controlling:
    - progression length
    - number of chord types
    - seventh chords
    - inversions
    - cadence complexity
    - secondary dominants
    - voice-leading complexity

18. The generator should be deterministic when given a random seed,
    so that exercises can be reproduced for testing.

19. Keep the harmonic grammar separate from the audio synthesis layer.
    A progression should be representable independently of its MIDI/audio
    realization.

20. Prefer pedagogically recognizable progressions over maximum randomness.
    Randomness should create variations of valid musical structures,
    not arbitrary chord sequences.