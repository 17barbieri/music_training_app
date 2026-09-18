from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QDialog,
    QGridLayout,
    QHeaderView,
    QGroupBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QStackedLayout,
    QHBoxLayout,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
    QScrollArea,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget

from app.audio.piano_player import PianoPlayer
from app.exercises.generator import IntervalGenerator
from app.exercises.interval import IntervalExercise
from app.exercises.confusion_matrix import ConfusionMatrix
from app.exercises.chord import ChordExercise
from app.exercises.chord_generator import ChordGenerator
from app.exercises.progression import ProgressionExercise
from app.exercises.progression_generator import ProgressionGenerator
from app.exercises.notation import LilyPondRenderer
from app.exercises.theory import (
    CHORDS,
    CHORD_PROFILES,
    INTERVAL_DIFFICULTIES,
    INTERVALS,
    PROGRESSIONS,
)


class MainWindow(QMainWindow):
    """Main application window."""

    def closeEvent(self, event) -> None:
        """Release the FluidSynth engine when the application exits."""

        self.audio.close()
        if self._notation_temporary_directory is not None:
            self._notation_temporary_directory.cleanup()
        event.accept()

    def __init__(self) -> None:
        super().__init__()

        self.audio = PianoPlayer()

        self.interval_generator = IntervalGenerator()
        self.chord_generator = ChordGenerator()
        self.progression_generator = ProgressionGenerator()
        self.notation_renderer: LilyPondRenderer | None = None
        self._notation_svg_path = None
        self._notation_temporary_directory = None
        self.confusion_matrix = ConfusionMatrix()

        self.current_exercise: (
            IntervalExercise | ChordExercise | ProgressionExercise | None
        ) = None
        self.progression_answer_index = 0
        self.chord_checkboxes: dict[str, QCheckBox] = {}
        self.selected_chords = list(CHORD_PROFILES["All triads"])

        # Temporary selection state for two-stage interval answers
        self._selected_nature: str | None = None
        self._selected_colour: str | None = None

        # Button references for visual feedback and checked state
        self._nature_buttons: dict[str, QPushButton] = {}
        self._colour_buttons: dict[str, QPushButton] = {}
        self._chord_type_buttons: dict[str, QPushButton] = {}
        self._chord_inversion_buttons: dict[int, QPushButton] = {}
        self._progression_degree_buttons: dict[str, QPushButton] = {}
        self._selected_chord_type: str | None = None
        self._selected_chord_inversion: int | None = None

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
        selection_layout.setContentsMargins(24, 24, 24, 20)
        selection_layout.setSpacing(8)

        title = QLabel("Harmony Trainer")
        title.setObjectName("title")

        subtitle = QLabel("Train your ear to recognize intervals, chords and harmonic progressions.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

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
        self.exercise_combo.setFixedWidth(360)
        self.exercise_combo.currentIndexChanged.connect(self._exercise_type_changed)
        exercise_layout.addWidget(self.exercise_combo, 0, 1, 1, 2)

        selection_layout.addWidget(exercise_group)

        self.options_group = QGroupBox("Exercise options")
        self.options_layout = QGridLayout(self.options_group)

        self.difficulty_label = QLabel("Difficulty:")
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Beginner", "Intermediate", "Advanced"])
        self.difficulty_combo.setFixedWidth(360)
        self.difficulty_combo.currentIndexChanged.connect(self._difficulty_changed)
        self.options_layout.addWidget(self.difficulty_label, 0, 0)
        self.options_layout.addWidget(self.difficulty_combo, 0, 1)

        self.chord_profile_label = QLabel("Chord profile:")
        self.chord_profile_combo = QComboBox()
        self.chord_profile_combo.addItems(CHORD_PROFILES)
        self.chord_profile_combo.currentTextChanged.connect(
            self._chord_profile_changed
        )
        self.options_layout.addWidget(self.chord_profile_label, 1, 0)
        self.options_layout.addWidget(self.chord_profile_combo, 1, 1)

        self.options_message = QLabel()
        self.options_layout.addWidget(self.options_message, 2, 0, 1, 2)

        selection_layout.addWidget(self.options_group)

        self.confirm_button = QPushButton("Start exercise")
        self.confirm_button.setMinimumHeight(40)
        self.confirm_button.clicked.connect(self._confirm_selection)
        selection_layout.addWidget(self.confirm_button)

        self.stacked_layout.addWidget(selection_page)

        # ---------- Exercise page ----------
        exercise_page = QWidget()
        exercise_page_layout = QVBoxLayout(exercise_page)
        # increase top margin so title/banner is fully visible
        exercise_page_layout.setContentsMargins(20, 14, 20, 12)
        exercise_page_layout.setSpacing(6)

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
        self.status_label.setMinimumHeight(30)
        current_layout.addWidget(self.status_label)

        self.play_button = QPushButton("▶  Play")
        self.play_button.setMinimumHeight(32)
        self.play_button.clicked.connect(self._play_current_exercise)
        current_layout.addWidget(self.play_button)

        chord_playback_layout = QHBoxLayout()
        self.play_chord_button = QPushButton("Play chord")
        self.play_chord_button.setCheckable(True)
        self.play_chord_button.setChecked(True)
        self.play_chord_button.clicked.connect(
            lambda: self._set_chord_playback_mode("chord")
        )
        chord_playback_layout.addWidget(self.play_chord_button)

        self.play_single_notes_button = QPushButton("Play single notes")
        self.play_single_notes_button.setCheckable(True)
        self.play_single_notes_button.clicked.connect(
            lambda: self._set_chord_playback_mode("single_notes")
        )
        chord_playback_layout.addWidget(self.play_single_notes_button)
        current_layout.addLayout(chord_playback_layout)

        self.progression_reveal = QLabel()
        self.progression_reveal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.progression_reveal)

        progression_playback_layout = QHBoxLayout()
        self.play_built_progression_button = QPushButton("Play built progression")
        self.play_built_progression_button.clicked.connect(
            lambda: self._play_progression(prefix_only=True)
        )
        progression_playback_layout.addWidget(self.play_built_progression_button)
        self.play_full_progression_button = QPushButton("Play full progression")
        self.play_full_progression_button.clicked.connect(
            lambda: self._play_progression(prefix_only=False)
        )
        progression_playback_layout.addWidget(self.play_full_progression_button)
        self.view_score_button = QPushButton("View score")
        self.view_score_button.clicked.connect(self._show_progression_notation)
        progression_playback_layout.addWidget(self.view_score_button)
        self.next_question_button = QPushButton("Next question")
        self.next_question_button.clicked.connect(self._after_progression)
        progression_playback_layout.addWidget(self.next_question_button)
        current_layout.addLayout(progression_playback_layout)

        answers_group = QGroupBox("Your answer")
        self.answers_layout = QGridLayout(answers_group)
        self.answers_scroll = QScrollArea()
        self.answers_scroll.setWidgetResizable(True)
        self.answers_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.answers_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.answers_scroll.setFixedHeight(140)
        self.answers_scroll.setWidget(answers_group)
        current_layout.addWidget(self.answers_scroll)

        exercise_page_layout.addWidget(current_group)

        self.score_label = QLabel("Score: 0 / 0")
        self.score_label.setObjectName("score")
        exercise_page_layout.addWidget(self.score_label)

        matrix_controls = QWidget()
        matrix_layout = QGridLayout(matrix_controls)
        matrix_layout.setContentsMargins(0, 0, 0, 0)
        matrix_layout.addWidget(QLabel("Confusion matrix:"), 0, 0)
        self.view_matrix_button = QPushButton("View matrix")
        self.view_matrix_button.clicked.connect(self._show_matrix)
        matrix_layout.addWidget(self.view_matrix_button, 0, 1)

        self.reset_matrix_button = QPushButton("Reset matrix")
        self.reset_matrix_button.setMinimumHeight(26)
        self.reset_matrix_button.clicked.connect(self._reset_current_matrix)
        matrix_layout.addWidget(self.reset_matrix_button, 0, 2)
        self.choose_chords_button = QPushButton("Choose chord types")
        self.choose_chords_button.clicked.connect(self._choose_chords)
        matrix_layout.addWidget(self.choose_chords_button, 1, 0, 1, 2)
        exercise_page_layout.addWidget(matrix_controls)

        self.stacked_layout.addWidget(exercise_page)

        # Initialize answers for current selection
        self._refresh_answers()
        self._refresh_matrix()
        self._refresh_exercise_options()
        self._update_chord_selection_visibility()
        self._update_progression_controls()

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
                padding: 8px;

                background: white;
            }

            QPushButton {
                min-height: 30px;
                padding: 4px 8px;

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
        self._update_chord_selection_visibility()
        self._refresh_exercise_options()
        if index == 1:
            self._chord_profile_changed(self.chord_profile_combo.currentText())

        if index == 0:
            self._generate_next_exercise()
        elif index == 2:
            self._generate_next_exercise()

        else:
            self.current_exercise = None

            self.status_label.setText(
                "This exercise type is not implemented yet."
            )
        self._update_progression_controls()

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

    def _chord_profile_changed(self, profile: str) -> None:
        """Apply a standard chord profile from the selection page."""

        self.selected_chords = list(CHORD_PROFILES[profile])
        if self.exercise_combo.currentIndex() == 1:
            self._refresh_answers()

    def _choose_chords(self) -> None:
        """Open the custom chord selection dialog."""

        dialog = QDialog(self)
        dialog.setWindowTitle("Choose chord types")
        layout = QVBoxLayout(dialog)
        checkboxes: dict[str, QCheckBox] = {}
        chord_layout = QGridLayout()

        for index, chord_name in enumerate(CHORDS):
            checkbox = QCheckBox(chord_name)
            checkbox.setChecked(chord_name in self.selected_chords)
            checkboxes[chord_name] = checkbox
            chord_layout.addWidget(checkbox, index // 3, index % 3)

        layout.addLayout(chord_layout)
        buttons = QHBoxLayout()
        apply_button = QPushButton("Apply")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(apply_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        apply_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_chords = [
            chord_name
            for chord_name, checkbox in checkboxes.items()
            if checkbox.isChecked()
        ]
        if not selected_chords:
            self.status_label.setText("Select at least one chord type.")
            return

        self.selected_chords = selected_chords
        self._refresh_answers()
        self._generate_next_exercise()

    def _update_chord_selection_visibility(self) -> None:
        is_chord_exercise = self.exercise_combo.currentIndex() == 1
        self.choose_chords_button.setVisible(is_chord_exercise)
        self.play_chord_button.setVisible(is_chord_exercise)
        self.play_single_notes_button.setVisible(is_chord_exercise)

    def _update_progression_controls(self) -> None:
        is_progression = self.exercise_combo.currentIndex() == 2
        progression_complete = (
            is_progression
            and isinstance(self.current_exercise, ProgressionExercise)
            and self.progression_answer_index >= len(self.current_exercise.degrees)
        )
        self.play_built_progression_button.setVisible(is_progression)
        self.play_full_progression_button.setVisible(is_progression)
        self.view_score_button.setVisible(progression_complete)
        self.next_question_button.setVisible(progression_complete)
        self.progression_reveal.setVisible(is_progression)
        if not is_progression:
            self.progression_reveal.clear()

    def _refresh_exercise_options(self) -> None:
        """Show only the options belonging to the selected exercise type."""

        exercise_index = self.exercise_combo.currentIndex()
        is_interval = exercise_index == 0
        is_chord = exercise_index == 1
        self.difficulty_label.setVisible(is_interval)
        self.difficulty_combo.setVisible(is_interval)
        self.chord_profile_label.setVisible(is_chord)
        self.chord_profile_combo.setVisible(is_chord)
        self.options_message.setVisible(exercise_index > 1)
        if exercise_index > 1:
            self.options_message.setText("No options are available yet.")

    def _selected_chords(self) -> list[str]:
        return list(self.selected_chords)

    @staticmethod
    def _chord_answers(chord_names: list[str]) -> list[str]:
        positions = [
            "Root position",
            "1st inversion",
            "2nd inversion",
            "3rd inversion",
        ]
        return [
            f"{chord_name} - {positions[inversion]}"
            for chord_name in chord_names
            for inversion in range(
                1 if chord_name == "Augmented" else len(CHORDS[chord_name])
            )
        ]

    def _confirm_selection(self) -> None:
        """Start the exercise page with the selected options."""

        exercise_type = self.exercise_combo.currentText()
        difficulty = self.difficulty_combo.currentText()

        self.exercise_title_label.setText(f"{exercise_type} — {difficulty}")

        # Ensure answers are updated for the selected exercise
        self._refresh_answers()

        # Generate the first exercise for the session
        if self.exercise_combo.currentIndex() in (0, 1, 2):
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

        self._nature_buttons.clear()
        self._colour_buttons.clear()
        self._chord_type_buttons.clear()
        self._chord_inversion_buttons.clear()
        self._progression_degree_buttons.clear()
        self._selected_chord_type = None
        self._selected_chord_inversion = None

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
            options = self._chord_answers(self._selected_chords())

        elif exercise_index == 2:
            options = ["I", "ii", "iii", "IV", "V", "vi", "vii"]

        else:
            options = PROGRESSIONS

        # If this is the interval exercise, present answers in two
        # compact groups: nature (2nd, 3rd, etc.) and quality
        # (Major/Minor). Perfect intervals are validated immediately
        # when their nature is clicked.
        if exercise_index == 0:
            # Nature buttons
            nature_group = QGroupBox("Nature")
            nature_layout = QGridLayout(nature_group)

            natures = [
                "2nd",
                "3rd",
                "4th",
                "5th",
                "Tritone",
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
                r = i // 4
                c = i % 4
                nature_layout.addWidget(btn, r, c)
                self._nature_buttons[name] = btn

            # Quality buttons
            colour_group = QGroupBox("Quality")
            colour_layout = QGridLayout(colour_group)

            colours = ["Minor", "Major"]

            for i, name in enumerate(colours):
                btn = QPushButton(name)
                btn.setCheckable(True)
                btn.setMinimumHeight(30)
                btn.setMaximumWidth(110)
                btn.clicked.connect(
                    lambda checked=False, value=name: self._colour_selected(value)
                )
                r = 0
                c = i
                colour_layout.addWidget(btn, r, c)
                self._colour_buttons[name] = btn

            # Place the two groups side-by-side
            self.answers_layout.addWidget(nature_group, 0, 0)
            self.answers_layout.addWidget(colour_group, 0, 1)

        elif exercise_index == 1:
            type_group = QGroupBox("Chord type")
            type_layout = QGridLayout(type_group)
            for index, chord_name in enumerate(self._selected_chords()):
                button = QPushButton(chord_name)
                button.setCheckable(True)
                button.clicked.connect(
                    lambda checked=False, value=chord_name: self._chord_type_selected(value)
                )
                type_layout.addWidget(button, index // 3, index % 3)
                self._chord_type_buttons[chord_name] = button

            inversion_group = QGroupBox("Inversion")
            inversion_layout = QGridLayout(inversion_group)
            inversions = [
                (0, "Root"),
                (1, "1st"),
                (2, "2nd"),
                (3, "3rd"),
            ]
            for index, (value, label) in enumerate(inversions):
                button = QPushButton(label)
                button.setCheckable(True)
                button.clicked.connect(
                    lambda checked=False, inversion=value: self._chord_inversion_selected(inversion)
                )
                inversion_layout.addWidget(button, 0, index)
                self._chord_inversion_buttons[value] = button

            self.answers_layout.addWidget(type_group, 0, 0)
            self.answers_layout.addWidget(inversion_group, 0, 1)
            self._update_chord_inversion_buttons()

        elif exercise_index == 2:
            progression_group = QGroupBox("Scale degree")
            progression_layout = QGridLayout(progression_group)
            for index, degree in enumerate(options):
                button = QPushButton(degree)
                button.setMinimumHeight(36)
                button.clicked.connect(
                    lambda checked=False, value=degree: self._progression_degree_selected(value)
                )
                progression_layout.addWidget(button, 0, index)
                self._progression_degree_buttons[degree] = button
            self.answers_layout.addWidget(progression_group, 0, 0)

        else:
            for index, answer in enumerate(options):
                button = QPushButton(answer)
                button.setMinimumHeight(40)
                if exercise_index == 1:
                    button.setFixedWidth(260)
                button.clicked.connect(
                    lambda checked=False, value=answer: self._answer_selected(value)
                )

                columns = 2 if exercise_index == 1 else 3
                row = index // columns
                column = index % columns

                self.answers_layout.addWidget(button, row, column)

        # Ensure layout updates
        self.answers_layout.update()
        self._refresh_matrix()

        # Styling for checked buttons and temporary feedback
        self.setStyleSheet(self.styleSheet() + "\n\n" +
            "QPushButton:checked { background: #d9d9d9; }\n" +
            "QPushButton.correct { background: #d4ffd4; }\n" +
            "QPushButton.incorrect { background: #ffd6d6; }\n"
        )

    def _nature_selected(self, nature: str) -> None:
        """Handle selection of interval nature (e.g. 2nd, 3rd).

        For perfect intervals (4th, 5th, Octave) and Tritone this
        immediately validates the answer.
        """

        # Map short names to the exact answer strings used by INTERVALS
        immediate_answers = {
            "4th": "Perfect 4th",
            "5th": "Perfect 5th",
            "Octave": "Octave",
            "Tritone": "Tritone",
        }

        # Normalize names like '2nd' -> '2nd' etc; for non-perfect we
        # wait for colour selection to disambiguate Major/Minor.
        if nature in immediate_answers:
            key = immediate_answers[nature]

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
        """Generate and store the next selected exercise."""

        difficulty = (
            self.difficulty_combo.currentText()
        )

        if self.exercise_combo.currentIndex() == 1:
            selected_chords = self._selected_chords()
            if not selected_chords:
                self.current_exercise = None
                self.status_label.setText("Select at least one chord type.")
                return
            self.current_exercise = self.chord_generator.generate(selected_chords)
        elif self.exercise_combo.currentIndex() == 2:
            self.current_exercise = self.progression_generator.generate()
            self.progression_answer_index = 0
            self.progression_reveal.setText("Your answer: (none yet)")
            self._prepare_progression_notation()
            self._update_progression_controls()
        else:
            allowed_intervals = INTERVAL_DIFFICULTIES[difficulty]
            self.current_exercise = self.interval_generator.generate(allowed_intervals)

        self.status_label.setText(
            "Press Play to hear the exercise."
        )

    def _prepare_progression_notation(self) -> None:
        """Create LilyPond source and rendering for the current progression."""

        if self._notation_temporary_directory is not None:
            self._notation_temporary_directory.cleanup()
            self._notation_temporary_directory = None
            self._notation_svg_path = None
        if not isinstance(self.current_exercise, ProgressionExercise):
            return
        try:
            if self.notation_renderer is None:
                self.notation_renderer = LilyPondRenderer()
            self._notation_svg_path, self._notation_temporary_directory = (
                self.notation_renderer.render(self.current_exercise)
            )
            self._notation_render_error = None
        except (FileNotFoundError, RuntimeError, OSError) as error:
            self._notation_render_error = str(error)

    def _refresh_matrix(self) -> None:
        """Display the persistent confusion matrix for the selected exercise."""

        if not hasattr(self, "matrix_table") or self.matrix_table is None:
            return

        exercise_type = self.exercise_combo.currentText()
        matrix = self.confusion_matrix.get(exercise_type)
        answer_order = [
            "Minor 2nd",
            "Major 2nd",
            "Minor 3rd",
            "Major 3rd",
            "Perfect 4th",
            "Perfect 5th",
            "Tritone",
            "Minor 6th",
            "Major 6th",
            "Minor 7th",
            "Major 7th",
            "Octave",
        ]
        answers_found = {
            answer
            for expected_answers in matrix.values()
            for answer in expected_answers
        } | set(matrix)
        if exercise_type == "Interval recognition":
            answers_found |= set(INTERVALS)
        answers = [
            answer for answer in answer_order if answer in answers_found
        ]
        answers.extend(sorted(answers_found - set(answers)))

        self.matrix_table.clear()
        self.matrix_table.setRowCount(len(answers))
        self.matrix_table.setColumnCount(len(answers))
        self.matrix_table.setVerticalHeaderLabels(answers)
        self.matrix_table.setHorizontalHeaderLabels(answers)

        for row, expected in enumerate(answers):
            total_answers = sum(matrix.get(expected, {}).values())
            for column, given in enumerate(answers):
                count = matrix.get(expected, {}).get(given, 0)
                item = QTableWidgetItem(str(count))
                if total_answers and count:
                    intensity = min(220, 40 + int(180 * count / total_answers))
                    if given == expected:
                        item.setBackground(
                            QBrush(QColor(80, 190, 105, intensity))
                        )
                    else:
                        item.setBackground(
                            QBrush(QColor(220, 85, 75, intensity))
                        )
                self.matrix_table.setItem(row, column, item)

    def _show_matrix(self) -> None:
        """Show the persistent confusion matrix in a separate window."""

        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"{self.exercise_combo.currentText()} confusion matrix"
        )
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            dialog.resize(
                min(1100, available.width() - 40),
                min(560, available.height() - 80),
            )
        else:
            dialog.resize(1100, 560)
        layout = QVBoxLayout(dialog)

        self.matrix_table = QTableWidget(dialog)
        self.matrix_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.matrix_table.setMinimumWidth(0)
        self.matrix_table.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )
        self.matrix_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.matrix_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.matrix_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.matrix_table.verticalHeader().setDefaultSectionSize(24)
        self.matrix_table.setMinimumHeight(330)
        layout.addWidget(self.matrix_table)

        color_bar = QLabel()
        color_bar.setFixedHeight(18)
        color_bar.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #dc554b, stop:0.5 #f5f5f5, stop:1 #50be69);"
        )
        layout.addWidget(color_bar)

        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Needs practice"))
        legend_layout.addStretch()
        legend_layout.addWidget(QLabel("Strong performance"))
        layout.addLayout(legend_layout)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        self._refresh_matrix()
        dialog.exec()
        self.matrix_table = None


    def _reset_current_matrix(self) -> None:
        """Reset the matrix for the selected exercise type."""

        exercise_type = self.exercise_combo.currentText()
        confirmation = QMessageBox.question(
            self,
            "Reset confusion matrix",
            f"Reset the {exercise_type} confusion matrix?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self.confusion_matrix.reset(exercise_type)
        self._refresh_matrix()

    def _play_current_exercise(self) -> None:
        """Play the currently generated exercise."""

        if self.current_exercise is None:
            return

        exercise = self.current_exercise

        self.status_label.setText(
            "Playing..."
        )

        if isinstance(exercise, ProgressionExercise):
            self._play_progression(prefix_only=False)
            return
        if isinstance(exercise, ChordExercise):
            if self.play_single_notes_button.isChecked():
                for midi_note in exercise.notes:
                    self.audio.play_note(midi_note, duration=0.7)
            else:
                self.audio.play_chord(exercise.notes, duration=1.0)
        else:
            self.audio.play_note(exercise.root_note, duration=0.7)
            self.audio.play_note(exercise.second_note, duration=0.7)

        self.status_label.setText(
            "What interval did you hear?"
            if isinstance(exercise, IntervalExercise)
            else "What chord did you hear?"
        )

    def _play_progression(self, prefix_only: bool) -> None:
        """Play the full progression or the answer prefix built so far."""

        exercise = self.current_exercise
        if not isinstance(exercise, ProgressionExercise):
            return
        end = self.progression_answer_index if prefix_only else len(exercise.chords)
        if end == 0:
            self.status_label.setText("Select at least one scale degree first.")
            return
        self.status_label.setText(
            "Playing built progression..." if prefix_only else "Playing full progression..."
        )
        for chord in exercise.chords[:end]:
            self.audio.play_chord(chord, duration=0.7)
        self.status_label.setText("What scale degrees did you hear?")

    def _show_progression_notation(self) -> None:
        """Render the current progression and show it in a separate window."""

        if not isinstance(self.current_exercise, ProgressionExercise):
            return
        if self._notation_svg_path is None:
            QMessageBox.warning(
                self,
                "Notation unavailable",
                getattr(self, "_notation_render_error", "Notation is not available."),
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Progression notation")
        renderer = QSvgRenderer(str(self._notation_svg_path))
        natural_size = renderer.defaultSize()
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            score_width = min(natural_size.width(), available.width() - 80)
            score_height = min(natural_size.height(), available.height() - 180)
        else:
            score_width = natural_size.width()
            score_height = natural_size.height()
        score_width = max(700, score_width)
        score_height = max(260, score_height)
        dialog.resize(score_width + 40, score_height + 90)
        layout = QVBoxLayout(dialog)
        score_scroll = QScrollArea(dialog)
        score_scroll.setWidgetResizable(False)
        score_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        notation = QSvgWidget(str(self._notation_svg_path), dialog)
        notation.setFixedSize(score_width, score_height)
        score_scroll.setWidget(notation)
        layout.addWidget(score_scroll)
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        dialog.exec()

    def _progression_degree_selected(self, degree: str) -> None:
        """Check the next progression degree and reveal the correct prefix."""

        exercise = self.current_exercise
        if not isinstance(exercise, ProgressionExercise):
            return
        index = self.progression_answer_index
        if index >= len(exercise.degrees):
            return

        correct = exercise.is_correct_at(index, degree)
        selected_button = self._progression_degree_buttons.get(degree)
        correct_button = self._progression_degree_buttons.get(
            exercise.degrees[index]
        )
        if selected_button is not None:
            selected_button.setStyleSheet(
                "background: #d4ffd4" if correct else "background: #ffd6d6"
            )
        if not correct and correct_button is not None:
            correct_button.setStyleSheet("background: #d4ffd4")
        QTimer.singleShot(1000, self._clear_progression_feedback)
        self.confusion_matrix.record(
            self.exercise_combo.currentText(),
            exercise.degrees[index],
            degree,
        )
        self.progression_answer_index += 1
        self.progression_reveal.setText(
            f"Answer so far: {exercise.revealed_answer(self.progression_answer_index)}"
        )
        self.status_label.setText(
            "Correct so far. Continue." if correct else
            f"That chord was {exercise.degrees[index]}. Continue."
        )

        if self.progression_answer_index == len(exercise.degrees):
            if all(
                exercise.degrees[position] == degree
                for position, degree in enumerate(exercise.degrees)
            ):
                self.correct_answers += 1
            self.total_questions += 1
            self._update_score()
            self._update_progression_controls()

    def _clear_progression_feedback(self) -> None:
        """Remove temporary progression answer colors after one second."""

        for button in self._progression_degree_buttons.values():
            button.setStyleSheet("")

    def _after_progression(self) -> None:
        self._clear_staged_selection()
        self._generate_next_exercise()
        self._update_progression_controls()

    def _set_chord_playback_mode(self, mode: str) -> None:
        """Select whether chord notes play together or sequentially."""

        play_single_notes = mode == "single_notes"
        self.play_single_notes_button.setChecked(play_single_notes)
        self.play_chord_button.setChecked(not play_single_notes)

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
        self.confusion_matrix.record(
            self.exercise_combo.currentText(),
            exercise.answer,
            answer,
        )
        self._refresh_matrix()

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
        self._clear_staged_selection()
        self._generate_next_exercise()

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

        for btn in self._chord_type_buttons.values():
            try:
                btn.setChecked(False)
                btn.setStyleSheet("")
            except Exception:
                pass

        for btn in self._chord_inversion_buttons.values():
            try:
                btn.setChecked(False)
                btn.setStyleSheet("")
            except Exception:
                pass

        for btn in self._progression_degree_buttons.values():
            try:
                btn.setChecked(False)
                btn.setStyleSheet("")
            except Exception:
                pass

        self._selected_nature = None
        self._selected_colour = None
        self._selected_chord_type = None
        self._selected_chord_inversion = None
        self._update_chord_inversion_buttons()

    def _show_feedback(self, given: str, correct: bool, correct_answer: str) -> None:
        """Visually mark selected and correct buttons.

        - Selected buttons are marked green if correct, red if incorrect.
        - The canonical correct buttons are also marked green.
        The markings clear after a short timeout.
        """

        if isinstance(self.current_exercise, ChordExercise):
            positions = {
                "Root position": 0,
                "1st inversion": 1,
                "2nd inversion": 2,
                "3rd inversion": 3,
            }

            def parse_chord(answer: str) -> tuple[str, int]:
                chord_type, position = answer.rsplit(" - ", 1)
                return chord_type, positions[position]

            given_type, given_inversion = parse_chord(given)
            correct_type, correct_inversion = parse_chord(correct_answer)
            selected_buttons = []
            correct_buttons = []
            if given_type in self._chord_type_buttons:
                selected_buttons.append(self._chord_type_buttons[given_type])
            if given_inversion in self._chord_inversion_buttons:
                selected_buttons.append(self._chord_inversion_buttons[given_inversion])
            if correct_type in self._chord_type_buttons:
                correct_buttons.append(self._chord_type_buttons[correct_type])
            if correct_inversion in self._chord_inversion_buttons:
                correct_buttons.append(self._chord_inversion_buttons[correct_inversion])

            for button in selected_buttons:
                button.setStyleSheet(
                    "background: #d4ffd4" if correct else "background: #ffd6d6"
                )
            for button in correct_buttons:
                button.setStyleSheet("background: #d4ffd4")
            QTimer.singleShot(700, self._clear_staged_selection)
            return

        # Helper to parse an answer into (colour, nature) or perfect nature
        def parse(ans: str):
            if ans == "Octave" or ans.startswith("Perfect "):
                # Perfect intervals
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

    def _chord_type_selected(self, chord_type: str) -> None:
        """Stage a chord type and evaluate when its inversion is known."""

        self._set_chord_type_checked(chord_type)
        self._selected_chord_type = chord_type
        self._update_chord_inversion_buttons()
        if chord_type == "Augmented":
            self._answer_selected("Augmented - Root position")
            return

        if self._selected_chord_inversion is not None and self._selected_chord_inversion >= len(CHORDS[chord_type]):
            self._chord_inversion_buttons[self._selected_chord_inversion].setChecked(False)
            self._selected_chord_inversion = None
        if self._selected_chord_inversion is not None:
            self._submit_chord_selection()

    def _chord_inversion_selected(self, inversion: int) -> None:
        """Stage an inversion and evaluate when its chord type is known."""

        if self._selected_chord_type == "Augmented":
            self._selected_chord_inversion = None
            self._update_chord_inversion_buttons()
            return

        if inversion not in self._chord_inversion_buttons:
            return

        self._selected_chord_inversion = inversion
        for value, button in self._chord_inversion_buttons.items():
            button.setChecked(value == inversion)
        if self._selected_chord_type is not None:
            self._submit_chord_selection()

    def _submit_chord_selection(self) -> None:
        if self._selected_chord_type is None or self._selected_chord_inversion is None:
            return
        self._answer_selected(
            f"{self._selected_chord_type} - "
            f"{['Root position', '1st inversion', '2nd inversion', '3rd inversion'][self._selected_chord_inversion]}"
        )

    def _set_chord_type_checked(self, chord_type: str) -> None:
        for name, button in self._chord_type_buttons.items():
            button.setChecked(name == chord_type)

    def _update_chord_inversion_buttons(self) -> None:
        chord_type = self._selected_chord_type
        if chord_type is None:
            for button in self._chord_inversion_buttons.values():
                button.setVisible(True)
            return

        inversion_count = len(CHORDS[chord_type])
        for inversion, button in self._chord_inversion_buttons.items():
            button.setVisible(inversion < inversion_count and chord_type != "Augmented")