from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.audio.sine_player import SineWavePlayer
from app.exercises.generator import IntervalGenerator
from app.exercises.interval import IntervalExercise
from app.exercises.theory import (
    CHORDS,
    INTERVAL_DIFFICULTIES,
    INTERVALS,
    PROGRESSIONS,
)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.audio = SineWavePlayer()

        self.interval_generator = IntervalGenerator()

        self.current_exercise: IntervalExercise | None = None

        # Temporary selection state for two-stage interval answers
        self._selected_nature: str | None = None

        self.total_questions = 0
        self.correct_answers = 0

        self.setWindowTitle("Harmony Trainer")
        self.resize(1000, 700)

        self._build_ui()

        # Generate the first question immediately.
        self._generate_next_exercise()

    def _build_ui(self) -> None:
        """Construct the application interface."""

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )

        main_layout.setSpacing(20)

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------

        title = QLabel("Harmony Trainer")

        title.setObjectName("title")

        subtitle = QLabel(
            "Train your ear to recognize intervals, "
            "chords and harmonic progressions."
        )

        subtitle.setObjectName("subtitle")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # ---------------------------------------------------------
        # Exercise selection
        # ---------------------------------------------------------

        exercise_group = QGroupBox("Exercise")

        exercise_layout = QGridLayout(
            exercise_group
        )

        exercise_layout.addWidget(
            QLabel("Exercise type:"),
            0,
            0,
        )

        self.exercise_combo = QComboBox()

        self.exercise_combo.addItems(
            [
                "Interval recognition",
                "Chord recognition",
                "Harmonic progression recognition",
            ]
        )

        self.exercise_combo.currentIndexChanged.connect(
            self._exercise_type_changed
        )

        exercise_layout.addWidget(
            self.exercise_combo,
            0,
            1,
            1,
            2,
        )

        exercise_layout.addWidget(
            QLabel("Difficulty:"),
            1,
            0,
        )

        self.difficulty_combo = QComboBox()

        self.difficulty_combo.addItems(
            [
                "Beginner",
                "Intermediate",
                "Advanced",
            ]
        )

        self.difficulty_combo.currentIndexChanged.connect(
            self._difficulty_changed
        )

        exercise_layout.addWidget(
            self.difficulty_combo,
            1,
            1,
            1,
            2,
        )

        main_layout.addWidget(
            exercise_group
        )

        # ---------------------------------------------------------
        # Current exercise
        # ---------------------------------------------------------

        current_group = QGroupBox(
            "Current exercise"
        )

        current_layout = QVBoxLayout(
            current_group
        )

        self.status_label = QLabel(
            "Press Play to hear the exercise."
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setMinimumHeight(
            100
        )

        current_layout.addWidget(
            self.status_label
        )

        self.play_button = QPushButton(
            "▶  Play"
        )

        self.play_button.setMinimumHeight(
            55
        )

        self.play_button.clicked.connect(
            self._play_current_exercise
        )

        current_layout.addWidget(
            self.play_button
        )

        # ---------------------------------------------------------
        # Answers
        # ---------------------------------------------------------

        answers_group = QGroupBox(
            "Your answer"
        )

        self.answers_layout = QGridLayout(
            answers_group
        )

        current_layout.addWidget(
            answers_group
        )

        main_layout.addWidget(
            current_group
        )

        # ---------------------------------------------------------
        # Score
        # ---------------------------------------------------------

        self.score_label = QLabel(
            "Score: 0 / 0"
        )

        self.score_label.setObjectName(
            "score"
        )

        main_layout.addWidget(
            self.score_label
        )

        self._refresh_answers()

        # ---------------------------------------------------------
        # Styling
        # ---------------------------------------------------------

        self.setStyleSheet(
            """
            QMainWindow {
                background: #f6f7f9;
            }

            QLabel#title {
                font-size: 30px;
                font-weight: 700;
            }

            QLabel#subtitle {
                font-size: 15px;
                color: #555555;
            }

            QLabel#score {
                font-size: 16px;
                font-weight: 600;
            }

            QGroupBox {
                font-size: 16px;
                font-weight: 600;

                border: 1px solid #d5d8dd;
                border-radius: 10px;

                margin-top: 10px;
                padding: 14px;

                background: white;
            }

            QPushButton {
                min-height: 44px;
                padding: 6px 14px;

                font-size: 14px;

                border-radius: 7px;
                border: 1px solid #c9cdd3;

                background: #ffffff;
            }

            QPushButton:hover {
                background: #eef1f5;
            }

            QComboBox {
                min-height: 38px;
                padding: 2px 8px;
            }
            """
        )

    def _exercise_type_changed(
        self,
        index: int,
    ) -> None:
        """Handle a change of exercise type."""

        self.total_questions = 0
        self.correct_answers = 0

        self._update_score()

        self._refresh_answers()

        if index == 0:
            self._generate_next_exercise()

        else:
            self.current_exercise = None

            self.status_label.setText(
                "This exercise type is not implemented yet."
            )

    def _difficulty_changed(
        self,
        index: int,
    ) -> None:
        """Handle a change of difficulty."""

        # Difficulty changes reset the current training session.
        self.total_questions = 0
        self.correct_answers = 0

        self._update_score()

        if self.exercise_combo.currentIndex() == 0:
            self._generate_next_exercise()

    def _refresh_answers(self) -> None:
        """Update answer buttons according to exercise type."""

        while self.answers_layout.count():
            item = self.answers_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        exercise_index = (
            self.exercise_combo.currentIndex()
        )

        if exercise_index == 0:
            options = list(
                INTERVALS.keys()
            )

        elif exercise_index == 1:
            options = list(
                CHORDS.keys()
            )

        else:
            options = PROGRESSIONS

        # If this is the interval exercise, present answers in two
        # compact groups: nature (2nd, 3rd, etc.) and colour
        # (Major/Minor). Perfect intervals are validated immediately
        # when their nature is clicked.
        if exercise_index == 0:
            # Nature buttons
            nature_group = QGroupBox("Nature")
            nature_layout = QGridLayout(nature_group)

            natures = [
                "Unison",
                "2nd",
                "3rd",
                "4th",
                "5th",
                "6th",
                "7th",
                "Octave",
            ]

            for i, name in enumerate(natures):
                btn = QPushButton(name)
                btn.setMinimumHeight(34)
                btn.setMaximumWidth(120)
                btn.clicked.connect(
                    lambda checked=False, value=name: self._nature_selected(value)
                )
                r = i // 2
                c = i % 2
                nature_layout.addWidget(btn, r, c)

            # Colour/quality buttons
            colour_group = QGroupBox("Quality")
            colour_layout = QGridLayout(colour_group)

            colours = ["Major", "Minor", "Diminished", "Tritone"]

            for i, name in enumerate(colours):
                btn = QPushButton(name)
                btn.setMinimumHeight(34)
                btn.setMaximumWidth(120)
                btn.clicked.connect(
                    lambda checked=False, value=name: self._colour_selected(value)
                )
                r = i // 2
                c = i % 2
                colour_layout.addWidget(btn, r, c)

            # Place the two groups side-by-side
            self.answers_layout.addWidget(nature_group, 0, 0)
            self.answers_layout.addWidget(colour_group, 0, 1)

        else:
            for index, answer in enumerate(options):
                button = QPushButton(answer)
                button.setMinimumHeight(40)
                button.clicked.connect(
                    lambda checked=False, value=answer: self._answer_selected(value)
                )

                row = index // 3
                column = index % 3

                self.answers_layout.addWidget(button, row, column)

        # Ensure layout updates
        self.answers_layout.update()

    def _nature_selected(self, nature: str) -> None:
        """Handle selection of interval nature (e.g. 2nd, 3rd).

        For perfect intervals (Unison, 4th, 5th, Octave) this
        immediately validates the answer.
        """

        # Map short names to the exact answer strings used by INTERVALS
        perfect_map = {
            "Unison": "Unison",
            "4th": "Perfect 4th",
            "5th": "Perfect 5th",
            "Octave": "Octave",
        }

        # Normalize names like '2nd' -> '2nd' etc; for non-perfect we
        # wait for colour selection to disambiguate Major/Minor.
        if nature in perfect_map or nature == "Unison":
            # Determine proper key
            if nature == "Unison":
                key = "Unison"
            elif nature == "Octave":
                key = "Octave"
            else:
                key = perfect_map.get(nature, nature)

            # Immediately evaluate as the user has given a perfect interval
            self._answer_selected(key)
            # clear any staged selection
            self._selected_nature = None
            return

        # For non-perfect intervals store selection and wait for quality
        # e.g. "2nd" + "Minor" -> "Minor 2nd"
        self._selected_nature = nature

        # Provide a small status cue
        self.status_label.setText(f"Selected: {nature}. Now choose Major/Minor.")

    def _colour_selected(self, colour: str) -> None:
        """Handle quality selection (Major/Minor) and combine with nature."""

        if self._selected_nature is None:
            # Nothing chosen yet — prompt the user to pick the nature first
            self.status_label.setText("Select the interval number first (e.g. 2nd, 3rd).")
            return

        # Map displayed nature to ordinal used in the INTERVALS keys
        ord_map = {
            "2nd": "2nd",
            "3rd": "3rd",
            "6th": "6th",
            "7th": "7th",
        }

        nature = self._selected_nature

        if nature not in ord_map:
            # Safety fallback
            self.status_label.setText("Invalid interval selection.")
            self._selected_nature = None
            return

        answer = f"{colour} {ord_map[nature]}"

        # Clear staged selection
        self._selected_nature = None

        # Evaluate
        self._answer_selected(answer)

    def _generate_next_exercise(self) -> None:
        """Generate and store the next interval exercise."""

        difficulty = (
            self.difficulty_combo.currentText()
        )

        allowed_intervals = (
            INTERVAL_DIFFICULTIES[difficulty]
        )

        self.current_exercise = (
            self.interval_generator.generate(
                allowed_intervals
            )
        )

        self.status_label.setText(
            "Press Play to hear the exercise."
        )

    def _play_current_exercise(self) -> None:
        """Play the currently generated interval."""

        if self.current_exercise is None:
            return

        exercise = self.current_exercise

        self.status_label.setText(
            "Playing..."
        )

        # First prototype: melodic interval.
        #
        # The first note is played, followed by the second note.
        self.audio.play_note(
            exercise.root_note,
            duration=0.7,
        )

        self.audio.play_note(
            exercise.second_note,
            duration=0.7,
        )

        self.status_label.setText(
            "What interval did you hear?"
        )

    def _answer_selected(
        self,
        answer: str,
    ) -> None:
        """Evaluate the user's answer and prepare the next exercise."""

        if self.current_exercise is None:
            return

        exercise = self.current_exercise

        self.total_questions += 1

        if exercise.is_correct(answer):
            self.correct_answers += 1

            self.status_label.setText(
                f"✓ Correct! It was a {exercise.answer}."
            )

        else:
            self.status_label.setText(
                f"✗ Incorrect. The answer was "
                f"{exercise.answer}."
            )

        self._update_score()

        # The current question has now been answered.
        # Generate a new one for the next round.
        self._generate_next_exercise()

    def _update_score(self) -> None:
        """Update the score display."""

        self.score_label.setText(
            f"Score: "
            f"{self.correct_answers} / "
            f"{self.total_questions}"
        )