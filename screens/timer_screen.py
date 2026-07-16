from theme.theme_manager import theme_manager

from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
)
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText

from kivy.clock import Clock
from kivy.app import App

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout

from theme.themed_screen import ThemedScreenMixin
from theme.palettes import (
    BACKGROUND,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BUTTON,
)


class PomodoroTimer:
    def __init__(self):
        self.work_duration = 25 * 60
        self.break_duration = 5 * 60

        self.remaining = self.work_duration

        self.is_running = False
        self.is_break = False

        self._event = None

    def start(self):
        if not self.is_running:
            self.is_running = True

            if self._event is None:
                self._event = Clock.schedule_interval(
                    self.update_timer,
                    1,
                )

    def pause(self):
        self.is_running = False

    def reset(self):
        self.is_running = False

        if self.is_break:
            self.remaining = self.break_duration
        else:
            self.remaining = self.work_duration

    def set_work_duration(self, minutes, seconds):
        total_seconds = (minutes * 60) + seconds

        if total_seconds <= 0:
            return

        self.work_duration = total_seconds

        if not self.is_break:
            self.remaining = self.work_duration

    def set_break_duration(self, minutes, seconds):
        total_seconds = (minutes * 60) + seconds

        if total_seconds <= 0:
            return

        self.break_duration = total_seconds

        if self.is_break:
            self.remaining = self.break_duration

    def tick(self):
        if self.remaining > 0:
            self.remaining -= 1
        else:
            self.switch_session()

    def switch_session(self):
        self.is_break = not self.is_break

        if self.is_break:
            self.remaining = self.break_duration
        else:
            self.remaining = self.work_duration

    def update_timer(self, dt):
        if self.is_running:
            self.tick()

    def get_time(self):
        minutes = self.remaining // 60
        seconds = self.remaining % 60
        return f"{minutes:02}:{seconds:02}"

    def get_session(self):
        return "Break Time" if self.is_break else "Focus Time"

    def get_total_for_current_session(self):
        return self.break_duration if self.is_break else self.work_duration


class TimerScreen(ThemedScreenMixin, MDScreen):

    THEME_MAP = {
        "self": ("md_bg_color", BACKGROUND),

        "header_label": ("text_color", TEXT_PRIMARY),
        "subtitle_label": ("text_color", TEXT_SECONDARY),

        "back_button": ("icon_color", TEXT_PRIMARY),

        "hourglass_icon": ("icon_color", BUTTON),

        "timer_label": ("text_color", TEXT_PRIMARY),

        "session_label": ("text_color", TEXT_PRIMARY),
        "session_sub_label": ("text_color", TEXT_SECONDARY),

        "reset_button": ("icon_color", TEXT_SECONDARY),
        "toggle_button": ("icon_color", BUTTON),
        "settings_button": ("icon_color", TEXT_SECONDARY),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.timer = PomodoroTimer()
        self.dialog = None

        Clock.schedule_interval(self.refresh_ui, 0.2)

    def refresh_ui(self, dt):
        self.ids.timer_label.text = self.timer.get_time()

        self.ids.session_label.text = self.timer.get_session()

        total_minutes = self.timer.get_total_for_current_session() // 60

        self.ids.session_sub_label.text = (
            f"{total_minutes} minute session"
        )

        self.ids.toggle_button.icon = (
            "pause"
            if self.timer.is_running
            else "play"
        )

    def toggle_timer(self):
        if self.timer.is_running:
            self.pause_timer()
        else:
            self.start_timer()

    def start_timer(self):
        self.timer.start()

    def pause_timer(self):
        self.timer.pause()

    def reset_timer(self):
        self.timer.reset()

    def go_back(self):
        App.get_running_app().root.current = "home"

    def on_theme_applied(self):
        """
        Reserved for future UI updates.
        ThemeManager will automatically apply THEME_MAP.
        """
        pass

    def open_timer_dialog(self):

        if self.dialog is None:

            self.minutes_field = MDTextField(
                mode="outlined",
                size_hint_x=None,
                width="95dp",
                size_hint_y=None,
                height="48dp",
                hint_text="Mins",
            )

            self.seconds_field = MDTextField(
                mode="outlined",
                size_hint_x=None,
                width="95dp",
                size_hint_y=None,
                height="48dp",
                hint_text="Secs",
            )

            self.break_minutes_field = MDTextField(
                mode="outlined",
                size_hint_x=None,
                width="95dp",
                size_hint_y=None,
                height="48dp",
                hint_text="Mins",
            )

            self.break_seconds_field = MDTextField(
                mode="outlined",
                size_hint_x=None,
                width="95dp",
                size_hint_y=None,
                height="48dp",
                hint_text="Secs",
            )

            focus_row = MDBoxLayout(
                orientation="horizontal",
                adaptive_height=True,
                adaptive_width=True,
                spacing="16dp",
                pos_hint={"center_x": 0.5},
            )

            focus_row.add_widget(self.minutes_field)
            focus_row.add_widget(self.seconds_field)

            break_row = MDBoxLayout(
                orientation="horizontal",
                adaptive_height=True,
                adaptive_width=True,
                spacing="16dp",
                pos_hint={"center_x": 0.5},
            )

            break_row.add_widget(self.break_minutes_field)
            break_row.add_widget(self.break_seconds_field)

            self.dialog = MDDialog(

                MDDialogHeadlineText(
                    text="Pomodoro Settings"
                ),

                MDDialogContentContainer(

                    MDDialogHeadlineText(
                        text="Set Focus Time"
                    ),

                    focus_row,

                    MDDialogHeadlineText(
                        text="Set Break Time"
                    ),

                    break_row,

                    orientation="vertical",
                ),

                MDDialogButtonContainer(

                    MDButton(
                        MDButtonText(text="Cancel"),
                        on_release=lambda x: self.dialog.dismiss(),
                    ),

                    MDButton(
                        MDButtonText(text="Set"),
                        style="filled",
                        on_release=self.apply_timer,
                    ),
                ),
            )

        self.dialog.open()

    def apply_timer(self, *args):

        work_minutes = (
            int(self.minutes_field.text)
            if self.minutes_field.text.isdigit()
            else 0
        )

        work_seconds = (
            int(self.seconds_field.text)
            if self.seconds_field.text.isdigit()
            else 0
        )

        break_minutes = (
            int(self.break_minutes_field.text)
            if self.break_minutes_field.text.isdigit()
            else 0
        )

        break_seconds = (
            int(self.break_seconds_field.text)
            if self.break_seconds_field.text.isdigit()
            else 0
        )

        work_seconds = min(work_seconds, 59)
        break_seconds = min(break_seconds, 59)

        self.timer.set_work_duration(
            work_minutes,
            work_seconds,
        )

        self.timer.set_break_duration(
            break_minutes,
            break_seconds,
        )

        self.dialog.dismiss()