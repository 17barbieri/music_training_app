from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QStackedLayout,
    QHBoxLayout,
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
        self._selected_colour: str | None = None

        # Button references for visual feedback and checked state
        self._nature_buttons: dict[str, QPushButton] = {}
        self._colour_buttons: dict[str, QPushButton] = {}

        self.total_questions = 0
        self.correct_answers = 0

        self.setWindowTitle("Harmony Trainer")
        # Determine a compact default window size based on available screen
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is not None:
                avail = screen.availableGeometry()
                # Pick a size that fits comfortably on most displays
                w = min(760, avail.width() - 80)
                h = min(460, avail.height() - 120)
            x = avail.x() + (avail.width() - w) // 2
            # move window a bit further down so the top banner is fully visible
            y = avail.y() + 30
            # Set geometry (position + size) atomically so layout/minimums
            # don't cause an unexpected resize later.
            self.setGeometry(x, y, w, h)
        except Exception:
            # Fall back to a conservative size if positioning fails
            self.resize(760, 460)

        self._build_ui()

        # Generate the first question immediately.
        self._generate_next_exercise()

    def _build_ui(self) -> None:
        """Construct the application interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Stacked layout: selection page (0) and exercise page (1)
        self.stacked_layout = QStackedLayout(central_widget)

        # ---------- Selection page ----------
        selection_page = QWidget()
        selection_layout = QVBoxLayout(selection_page)
        # increase top margin so title/banner is fully visible
        selection_layout.setContentsMargins(32, 48, 32, 28)
        selection_layout.setSpacing(12)

        title = QLabel("Harmony Trainer")
        title.setObjectName("title")

        subtitle = QLabel("Train your ear to recognize intervals, chords and harmonic progressions.")
        subtitle.setObjectName("subtitle")

        selection_layout.addWidget(title)
        selection_layout.addWidget(subtitle)

        # Exercise selection group (on selection page)
        exercise_group = QGroupBox("Exercise")
        exercise_layout = QGridLayout(exercise_group)

        exercise_layout.addWidget(QLabel("Exercise type:"), 0, 0)

        self.exercise_combo = QComboBox()
        self.exercise_combo.addItems([
            "Interval recognition",
            "Chord recognition",
            "Harmonic progression recognition",
        ])
        self.exercise_combo.currentIndexChanged.connect(self._exercise_type_changed)
        exercise_layout.addWidget(self.exercise_combo, 0, 1, 1, 2)

        exercise_layout.addWidget(QLabel("Difficulty:"), 1, 0)

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Beginner", "Intermediate", "Advanced"])
        self.difficulty_combo.currentIndexChanged.connect(self._difficulty_changed)
        exercise_layout.addWidget(self.difficulty_combo, 1, 1, 1, 2)

        selection_layout.addWidget(exercise_group)

        self.confirm_button = QPushButton("Start exercise")
        self.confirm_button.setMinimumHeight(40)
        self.confirm_button.clicked.connect(self._confirm_selection)
        selection_layout.addWidget(self.confirm_button)

        self.stacked_layout.addWidget(selection_page)

        # ---------- Exercise page ----------
        exercise_page = QWidget()
        exercise_page_layout = QVBoxLayout(exercise_page)
        # increase top margin so title/banner is fully visible
        exercise_page_layout.setContentsMargins(32, 48, 32, 28)
        exercise_page_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        self.back_button = QPushButton("← Back")
        self.back_button.setMinimumHeight(34)
        self.back_button.clicked.connect(self._go_back)
        top_bar.addWidget(self.back_button)

        self.exercise_title_label = QLabel("")
        self.exercise_title_label.setObjectName("subtitle")
        top_bar.addWidget(self.exercise_title_label)
        top_bar.addStretch()

        exercise_page_layout.addLayout(top_bar)

        current_group = QGroupBox("Current exercise")
        current_layout = QVBoxLayout(current_group)

        self.status_label = QLabel("Press Play to hear the exercise.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(80)
        current_layout.addWidget(self.status_label)

        self.play_button = QPushButton("▶  Play")
        self.play_button.setMinimumHeight(44)
        self.play_button.clicked.connect(self._play_current_exercise)
        current_layout.addWidget(self.play_button)

        answers_group = QGroupBox("Your answer")
        self.answers_layout = QGridLayout(answers_group)
        current_layout.addWidget(answers_group)

        exercise_page_layout.addWidget(current_group)

        self.score_label = QLabel("Score: 0 / 0")
        self.score_label.setObjectName("score")
        exercise_page_layout.addWidget(self.score_label)

        self.stacked_layout.addWidget(exercise_page)

        # Initialize answers for current selection
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

            "QPushButton {
                min-height: 36px;
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

    def _confirm_selection(self) -> None:
        """Start the exercise page with the selected options."""

        exercise_type = self.exercise_combo.currentText()
        difficulty = self.difficulty_combo.currentText()

        self.exercise_title_label.setText(f"{exercise_type} — {difficulty}")

        # Ensure answers are updated for the selected exercise
        self._refresh_answers()

        # Generate the first exercise for the session
        if self.exercise_combo.currentIndex() == 0:
            # reset scores for new session
            self.total_questions = 0
            self.correct_answers = 0
            self._update_score()
            self._generate_next_exercise()

        # Switch to exercise page
        self.stacked_layout.setCurrentIndex(1)

    def _go_back(self) -> None:
        """Return to the selection page."""

        self.stacked_layout.setCurrentIndex(0)

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
                btn.setCheckable(True)
                btn.setMinimumHeight(30)
                btn.setMaximumWidth(110)
                btn.clicked.connect(
                    lambda checked=False, value=name: self._nature_selected(value)
                )
                r = i // 2
                c = i % 2
                nature_layout.addWidget(btn, r, c)
                self._nature_buttons[name] = btn

            # Colour/quality buttons
            colour_group = QGroupBox("Quality")
            colour_layout = QGridLayout(colour_group)

            colours = ["Major", "Minor", "Diminished", "Tritone"]

            for i, name in enumerate(colours):
                btn = QPushButton(name)
                btn.setCheckable(True)
                btn.setMinimumHeight(30)
                btn.setMaximumWidth(110)
                btn.clicked.connect(
                    lambda checked=False, value=name: self._colour_selected(value)
                )
                r = i // 2
                c = i % 2
                colour_layout.addWidget(btn, r, c)
                self._colour_buttons[name] = btn

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

        # Styling for checked buttons and temporary feedback
        self.setStyleSheet(self.styleSheet() + "\n\n" +
            "QPushButton:checked { background: #d9d9d9; }\n" +
            "QPushButton.correct { background: #d4ffd4; }\n" +
            "QPushButton.incorrect { background: #ffd6d6; }\n"
        )

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
            # Provide a checked/visual cue briefly
            btn = self._nature_buttons.get(nature)
            if btn:
                btn.setChecked(True)

            self._answer_selected(key)
            # clear any staged selection
            self._selected_nature = None
            self._selected_colour = None
            QTimer.singleShot(600, self._clear_staged_selection)
            return

        # For non-perfect intervals store selection and wait for quality
        # e.g. "2nd" + "Minor" -> "Minor 2nd"
        # Toggle selection state on the pressed button
        # Uncheck previous if any
        if self._selected_nature and self._selected_nature in self._nature_buttons:
            self._nature_buttons[self._selected_nature].setChecked(False)

        self._selected_nature = nature
        if nature in self._nature_buttons:
            self._nature_buttons[nature].setChecked(True)

        # If a colour was already selected, combine immediately
        if self._selected_colour:
            answer = f"{self._selected_colour} {nature}"
            # Clear staged selection after evaluating
            self._answer_selected(answer)
            self._selected_nature = None
            self._selected_colour = None
            QTimer.singleShot(600, self._clear_staged_selection)
            return

        # Provide a small status cue
        self.status_label.setText(f"Selected: {nature}. Now choose Major/Minor.")

    def _colour_selected(self, colour: str) -> None:
        """Handle quality selection (Major/Minor) and combine with nature."""

        # If a nature was already selected, combine immediately
        if self._selected_nature:
            # The nature is something like '2nd' or '3rd'
            answer = f"{colour} {self._selected_nature}"
            # Provide checked cue for colour button
            if self._selected_colour and self._selected_colour in self._colour_buttons:
                self._colour_buttons[self._selected_colour].setChecked(False)

            self._selected_colour = colour
            if colour in self._colour_buttons:
                self._colour_buttons[colour].setChecked(True)

            self._answer_selected(answer)
            self._selected_nature = None
            self._selected_colour = None
            QTimer.singleShot(600, self._clear_staged_selection)
            return

        # Otherwise store selected colour and wait for nature
        if self._selected_colour and self._selected_colour in self._colour_buttons:
            self._colour_buttons[self._selected_colour].setChecked(False)

        self._selected_colour = colour
        if colour in self._colour_buttons:
            self._colour_buttons[colour].setChecked(True)

        self.status_label.setText(f"Selected: {colour}. Now choose the interval number.")
        return
        

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

        # Evaluate
        correct = exercise.is_correct(answer)

        self.total_questions += 1

        if correct:
            self.correct_answers += 1
            self.status_label.setText(f"✓ Correct! It was a {exercise.answer}.")
        else:
            self.status_label.setText(
                f"✗ Incorrect. The answer was {exercise.answer}."
            )

        # Show visual feedback on the selected and correct buttons,
        # then update score and generate the next exercise after a short delay.
        self._show_feedback(answer, correct, exercise.answer)

        QTimer.singleShot(700, self._after_feedback)

    def _after_feedback(self) -> None:
        """Actions to perform after feedback display: update score and next exercise."""

        self._update_score()
        self._generate_next_exercise()
        self._clear_staged_selection()

    def _clear_staged_selection(self) -> None:
        """Clear any staged selections and reset button states/styles."""

        for btn in self._nature_buttons.values():
            try:
                btn.setChecked(False)
                btn.setStyleSheet("")
            except Exception:
                pass

        for btn in self._colour_buttons.values():
            try:
                btn.setChecked(False)
                btn.setStyleSheet("")
            except Exception:
                pass

        self._selected_nature = None
        self._selected_colour = None

    def _show_feedback(self, given: str, correct: bool, correct_answer: str) -> None:
        """Visually mark selected and correct buttons.

        - Selected buttons are marked green if correct, red if incorrect.
        - The canonical correct buttons are also marked green.
        The markings clear after a short timeout.
        """

        # Helper to parse an answer into (colour, nature) or perfect nature
        def parse(ans: str):
            if ans in ("Unison", "Octave") or ans.startswith("Perfect "):
                # Perfect intervals
                if ans == "Unison":
                    return (None, "Unison")
                if ans == "Octave":
                    return (None, "Octave")
                # e.g. 'Perfect 4th' -> ('Perfect', '4th') but nature button is '4th'
                parts = ans.split()
                return (None, parts[-1])
            parts = ans.split(" ", 1)
            if len(parts) == 2:
                colour, nature = parts
                return (colour, nature)
            return (None, ans)

        given_colour, given_nature = parse(given)
        corr_colour, corr_nature = parse(correct_answer)

        selected_btns = []
        correct_btns = []

        if given_nature and given_nature in self._nature_buttons:
            selected_btns.append(self._nature_buttons[given_nature])
        if given_colour and given_colour in self._colour_buttons:
            selected_btns.append(self._colour_buttons[given_colour])

        if corr_nature and corr_nature in self._nature_buttons:
            correct_btns.append(self._nature_buttons[corr_nature])
        if corr_colour and corr_colour in self._colour_buttons:
            correct_btns.append(self._colour_buttons[corr_colour])

        # Apply styles
        for btn in selected_btns:
            if correct:
                btn.setStyleSheet("background: #d4ffd4")
            else:
                btn.setStyleSheet("background: #ffd6d6")

        for btn in correct_btns:
            btn.setStyleSheet("background: #d4ffd4")

        # Clear styles shortly after
        QTimer.singleShot(700, self._clear_staged_selection)

    def _update_score(self) -> None:
        """Update the score display."""

        self.score_label.setText(
            f"Score: "
            f"{self.correct_answers} / "
            f"{self.total_questions}"
        )