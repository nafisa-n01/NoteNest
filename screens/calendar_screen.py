# screens/calendar_screen.py
"""
Calendar screen -- simple date-based reminders, with an optional
recurring mode: an incomplete recurring reminder shifts to today
every time the calendar is opened, and shows a "Missed N days" tag
until it's marked done.

MDScreen + calendar_screen.kv, matching settings_screen.py's pattern.
Talks only to database/calendar_queries.py -- no dependency on
tasks, categories, or reminders (those stay owned by other
screens/teammates).
"""

import calendar
import webbrowser
from datetime import datetime

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton

from database.calendar_queries import (
    create_calendar_events_table,
    create_event,
    delete_event,
    get_all_event_dates,
    get_events_by_date,
    mark_event_completed,
    roll_forward_recurring_events,
    update_event,
)
from theme.palettes import (
    ACCENT,
    BACKGROUND,
    BORDER,
    CARD_PRIMARY,
    CARD_SECONDARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from theme.theme_manager import theme_manager
from theme.themed_screen import ThemedScreenMixin


def theme_rgba(token):
    return get_color_from_hex(theme_manager.get_color(token))


# ---------------------------------------------------------------------------
# Small building-block widgets
# ---------------------------------------------------------------------------

class CalendarDayCell(ButtonBehavior, BoxLayout):
    """
    One date cell in the month grid.
    - Selected day: filled accent circle behind the number.
    - Today (not selected): thin accent ring instead of a fill.
    - Has an event: small dot under the number.
    """

    day_number = StringProperty("")
    date_value = StringProperty("")
    is_today = BooleanProperty(False)
    is_selected = BooleanProperty(False)
    has_event = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        with self.canvas.before:
            self._fill_color = Color(0, 0, 0, 0)
            self._fill = Ellipse(pos=self.pos, size=self.size)
        with self.canvas.after:
            self._dot_color = Color(0, 0, 0, 0)
            self._dot = Ellipse(pos=self.pos, size=(dp(4), dp(4)))

        self.number_label = Label(
            text=self.day_number,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(28),
        )
        self.add_widget(self.number_label)

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            day_number=self._sync_text,
            is_today=self._refresh_theme,
            is_selected=self._refresh_theme,
            has_event=self._redraw,
        )
        theme_manager.bind(theme_name=self._refresh_theme)
        self._refresh_theme()

    def _sync_text(self, *_args):
        self.number_label.text = self.day_number

    def _redraw(self, *_args):
        side = min(self.width, dp(34))
        cx = self.center_x - side / 2
        cy = self.top - side - dp(2)
        self._fill.pos = (cx, cy)
        self._fill.size = (side, side)
        self._dot.pos = (self.center_x - dp(2), cy - dp(8))
        self._dot.size = (dp(4), dp(4))

    def _refresh_theme(self, *_args):
        if self.is_selected:
            self._fill_color.rgba = theme_rgba(ACCENT)
        elif self.is_today:
            accent = theme_rgba(ACCENT)
            self._fill_color.rgba = (accent[0], accent[1], accent[2], 0.28)
        else:
            self._fill_color.rgba = (0, 0, 0, 0)

        self._dot_color.rgba = theme_rgba(ACCENT) if self.has_event else (0, 0, 0, 0)

        self.number_label.color = theme_rgba(TEXT_PRIMARY)
        self._redraw()


class EventRow(ButtonBehavior, BoxLayout):
    """
    One reminder in the selected day's agenda -- colored left bar,
    complete-checkbox, title (+ strikethrough when done), time and/or
    a "Missed N days" tag, and an optional "open link" button.
    Tapping the row body (not the checkbox/link button) opens edit/delete.
    """

    def __init__(self, event, bar_token, on_tap, on_toggle_complete, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(64))
        kwargs.setdefault("spacing", dp(10))
        kwargs.setdefault("padding", [dp(2), dp(8), dp(4), dp(8)])
        super().__init__(**kwargs)

        self.event = event
        self.on_tap = on_tap
        self.on_toggle_complete = on_toggle_complete
        completed = event.get("completed", False)

        bar = Widget(size_hint_x=None, width=dp(3))
        with bar.canvas:
            bar_color = Color(*theme_rgba(bar_token))
            from kivy.graphics import RoundedRectangle
            bar_rect = RoundedRectangle(pos=bar.pos, size=bar.size, radius=[dp(1.5)])
        bar.bind(
            pos=lambda w, _v: setattr(bar_rect, "pos", w.pos),
            size=lambda w, _v: setattr(bar_rect, "size", w.size),
        )
        theme_manager.bind(
            theme_name=lambda *_a: setattr(bar_color, "rgba", theme_rgba(bar_token))
        )
        self.add_widget(bar)

        self.check_btn = MDIconButton(
            icon="checkbox-marked" if completed else "checkbox-blank-outline",
            theme_icon_color="Custom",
            icon_color=theme_rgba(ACCENT) if completed else theme_rgba(TEXT_SECONDARY),
            pos_hint={"center_y": 0.5},
        )
        self.check_btn.bind(on_release=lambda *_a: self._toggle_complete())
        self.add_widget(self.check_btn)

        text_box = BoxLayout(orientation="vertical")
        title = event.get("title", "")
        self.title_label = Label(
            text=f"[s]{title}[/s]" if completed else title,
            markup=True,
            font_size=sp(14),
            halign="left",
            valign="middle",
            color=theme_rgba(TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(24),
        )
        self.title_label.bind(size=self.title_label.setter("text_size"))

        time_text = event.get("event_time") or "Any time"
        missed_days = event.get("missed_days") or 0
        if not completed and missed_days:
            missed_text = "Missed yesterday" if missed_days == 1 else f"Missed {missed_days} days"
            meta_text = f"{time_text}   \u2022   {missed_text}"
        else:
            meta_text = time_text

        self.meta_label = Label(
            text=meta_text,
            font_size=sp(11),
            halign="left",
            valign="middle",
            color=theme_rgba(TEXT_SECONDARY),
            size_hint_y=None,
            height=dp(20),
        )
        self.meta_label.bind(size=self.meta_label.setter("text_size"))

        text_box.add_widget(self.title_label)
        text_box.add_widget(self.meta_label)
        self.add_widget(text_box)

        if event.get("event_link"):
            link_btn = MDIconButton(
                icon="open-in-new",
                theme_icon_color="Custom",
                icon_color=theme_rgba(ACCENT),
                pos_hint={"center_y": 0.5},
            )
            link_btn.bind(on_release=lambda *_a: self._open_link())
            self.add_widget(link_btn)

    def _open_link(self):
        link = (self.event.get("event_link") or "").strip()
        if not link:
            return
        if not link.startswith(("http://", "https://")):
            link = "https://" + link
        webbrowser.open(link)

    def _toggle_complete(self):
        if self.on_toggle_complete:
            self.on_toggle_complete(self.event)

    def on_release(self):
        if self.on_tap:
            self.on_tap(self.event)


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------

class CalendarScreen(ThemedScreenMixin, MDScreen):

    THEME_MAP = {
        "self":            ("md_bg_color", BACKGROUND),
        "title_label":     ("text_color", TEXT_PRIMARY),
        "subtitle_label":  ("text_color", TEXT_SECONDARY),
        "back_button":     ("icon_color", TEXT_PRIMARY),
        "add_button":      ("icon_color", ACCENT),
        "prev_button":     ("icon_color", TEXT_PRIMARY),
        "next_button":     ("icon_color", TEXT_PRIMARY),
        "today_button":    ("icon_color", ACCENT),
        "month_label":     ("text_color", TEXT_PRIMARY),
        "month_card":      ("md_bg_color", CARD_PRIMARY),
        "agenda_card":     ("md_bg_color", CARD_PRIMARY),
        "agenda_title":    ("text_color", TEXT_PRIMARY),
        "view_all_label":  ("text_color", ACCENT),
        "empty_label":     ("text_color", TEXT_SECONDARY),
    }

    _BAR_TOKENS = (ACCENT, TEXT_SECONDARY)

    def __init__(self, **kwargs):
        create_calendar_events_table()

        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        self.selected_date = now.strftime("%Y-%m-%d")
        self.day_cells = {}
        # Set by HomeScreen when routing here -- unused by this
        # reminder-based calendar, kept only so that attribute
        # assignment from home_screen.py doesn't fail.
        self.selected_task_id = None

        super().__init__(**kwargs)

    def _user_id(self):
        try:
            from kivy.app import App
            app = App.get_running_app()
            return getattr(app, "user_id", 1)
        except Exception:
            return 1

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._build_weekday_header()
        roll_forward_recurring_events(self._user_id())
        self.build_month_grid()
        self.select_date(self.selected_date)

    def on_pre_enter(self, *_args):
        roll_forward_recurring_events(self._user_id())
        self.build_month_grid()
        self.select_date(self.selected_date)

    def _build_weekday_header(self):
        header = self.ids.get("weekday_header")
        if header is None or header.children:
            return
        for name in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
            header.add_widget(
                Label(
                    text=name,
                    font_size=sp(10),
                    bold=True,
                    color=theme_rgba(TEXT_SECONDARY),
                    size_hint_y=None,
                    height=dp(20),
                )
            )

    def build_month_grid(self):
        grid = self.ids.get("day_grid")
        if grid is None:
            return
        grid.clear_widgets()
        self.day_cells = {}

        first_day = datetime(self.current_year, self.current_month, 1)
        self.ids.month_label.text = first_day.strftime("%B %Y")

        event_dates = get_all_event_dates(
            self.current_year, self.current_month, self._user_id()
        )
        weeks = calendar.monthcalendar(self.current_year, self.current_month)
        while len(weeks) < 6:
            weeks.append([0] * 7)

        today_value = datetime.now().strftime("%Y-%m-%d")

        for week in weeks[:6]:
            for day in week:
                if day == 0:
                    grid.add_widget(Widget())
                    continue
                date_value = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"
                cell = CalendarDayCell(
                    day_number=str(day),
                    date_value=date_value,
                    is_today=date_value == today_value,
                    has_event=date_value in event_dates,
                    is_selected=date_value == self.selected_date,
                )
                cell.bind(
                    on_release=lambda _cell, selected=date_value: self.select_date(selected)
                )
                self.day_cells[date_value] = cell
                grid.add_widget(cell)

    def select_date(self, date_value):
        self.selected_date = date_value
        for value, cell in self.day_cells.items():
            cell.is_selected = value == date_value

        selected = datetime.strptime(date_value, "%Y-%m-%d")
        self.ids.agenda_title.text = selected.strftime("%A, %d %B")
        self.refresh_agenda()

    def refresh_agenda(self):
        agenda_list = self.ids.get("agenda_list")
        if agenda_list is None:
            return
        agenda_list.clear_widgets()

        events = get_events_by_date(self.selected_date, self._user_id())

        if not events:
            empty = Label(
                text="No reminders for this date.",
                font_size=sp(12),
                color=theme_rgba(TEXT_SECONDARY),
                size_hint_y=None,
                height=dp(60),
            )
            agenda_list.add_widget(empty)
            return

        for index, event in enumerate(events):
            bar_token = self._BAR_TOKENS[index % len(self._BAR_TOKENS)]
            agenda_list.add_widget(
                EventRow(
                    event=event,
                    bar_token=bar_token,
                    on_tap=self.open_edit_popup,
                    on_toggle_complete=self.toggle_event_completed,
                )
            )

    def toggle_event_completed(self, event):
        mark_event_completed(event["id"], not event.get("completed", False))
        self.build_month_grid()
        self.select_date(self.selected_date)

    # -- navigation --
    def go_back(self):
        if self.manager:
            self.manager.current = "home"

    def go_to_today(self):
        today = datetime.now()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date = today.strftime("%Y-%m-%d")
        self.build_month_grid()
        self.select_date(self.selected_date)

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.selected_date = f"{self.current_year:04d}-{self.current_month:02d}-01"
        self.build_month_grid()
        self.select_date(self.selected_date)

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.selected_date = f"{self.current_year:04d}-{self.current_month:02d}-01"
        self.build_month_grid()
        self.select_date(self.selected_date)

    # -- add / edit popups --
    def open_add_popup(self):
        self._open_event_popup(mode="add")

    def open_add_task_popup(self, activity_type=None):
        """Compatibility shim for HomeScreen's Quick Add -- see
        earlier note in this file's history for why this exists."""
        self.open_add_popup()

    def open_edit_popup(self, event):
        self._open_event_popup(mode="edit", event=event)

    def _open_event_popup(self, mode, event=None):
        panel = MDCard(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(10),
            size_hint=(1, 1),
            theme_bg_color="Custom",
            md_bg_color=theme_manager.get_color(CARD_PRIMARY),
            radius=[18],
        )

        heading = Label(
            text="Add Reminder" if mode == "add" else "Edit Reminder",
            font_size=sp(17),
            bold=True,
            color=theme_rgba(TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
        )
        heading.bind(size=heading.setter("text_size"))
        panel.add_widget(heading)

        title_input = TextInput(
            text=event.get("title", "") if event else "",
            hint_text="Reminder title",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
        )
        panel.add_widget(title_input)

        time_input = TextInput(
            text=event.get("event_time") or "" if event else "",
            hint_text="HH:MM (optional, 24-hour)",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
        )
        panel.add_widget(time_input)

        link_input = TextInput(
            text=event.get("event_link") or "" if event else "",
            hint_text="Link (optional, e.g. https://...)",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
        )
        panel.add_widget(link_input)

        # -- recurring toggle row --
        recurring_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8),
        )
        recurring_state = {
            "value": bool(event.get("is_recurring")) if event else False
        }
        recurring_label = Label(
            text="Repeat daily until marked done",
            font_size=sp(11),
            color=theme_rgba(TEXT_SECONDARY),
            halign="left",
            valign="middle",
        )
        recurring_label.bind(size=recurring_label.setter("text_size"))
        recurring_toggle_btn = MDIconButton(
            icon="toggle-switch" if recurring_state["value"] else "toggle-switch-off-outline",
            theme_icon_color="Custom",
            icon_color=theme_rgba(ACCENT) if recurring_state["value"] else theme_rgba(TEXT_SECONDARY),
        )

        def toggle_recurring(*_args):
            recurring_state["value"] = not recurring_state["value"]
            recurring_toggle_btn.icon = (
                "toggle-switch" if recurring_state["value"] else "toggle-switch-off-outline"
            )
            recurring_toggle_btn.icon_color = (
                theme_rgba(ACCENT) if recurring_state["value"] else theme_rgba(TEXT_SECONDARY)
            )

        recurring_toggle_btn.bind(on_release=toggle_recurring)
        recurring_row.add_widget(recurring_label)
        recurring_row.add_widget(recurring_toggle_btn)
        panel.add_widget(recurring_row)

        error_label = Label(
            text="",
            font_size=sp(10),
            color=theme_rgba(TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        error_label.bind(size=error_label.setter("text_size"))
        panel.add_widget(error_label)

        actions = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(8),
        )

        popup = Popup(
            title="",
            content=panel,
            size_hint=(0.82, None),
            height=dp(370) if mode == "add" else dp(410),
            auto_dismiss=True,
            separator_height=0,
            background="",
            background_color=(0, 0, 0, 0),
        )

        cancel_btn = MDButton(style="tonal", on_release=lambda *_a: popup.dismiss())
        cancel_btn.add_widget(MDButtonText(text="Cancel"))
        actions.add_widget(cancel_btn)

        if mode == "edit":
            delete_btn = MDButton(
                style="tonal",
                on_release=lambda *_a: self._confirm_delete(popup, event["id"]),
            )
            delete_btn.add_widget(MDButtonText(text="Delete"))
            actions.add_widget(delete_btn)

        save_btn = MDButton(style="filled")
        save_btn.add_widget(MDButtonText(text="Save"))
        actions.add_widget(save_btn)

        def do_save(*_args):
            title = title_input.text.strip()
            time_value = time_input.text.strip()
            link_value = link_input.text.strip()
            is_recurring = recurring_state["value"]

            if not title:
                error_label.text = "Please enter a title."
                return
            if time_value:
                try:
                    datetime.strptime(time_value, "%H:%M")
                except ValueError:
                    error_label.text = "Time must use 24-hour HH:MM."
                    return

            if mode == "add":
                create_event(
                    user_id=self._user_id(),
                    title=title,
                    event_date=self.selected_date,
                    event_time=time_value or None,
                    event_link=link_value or None,
                    is_recurring=is_recurring,
                )
            else:
                update_event(
                    event["id"], title, time_value or None, link_value or None, is_recurring,
                )

            popup.dismiss()
            self.build_month_grid()
            self.select_date(self.selected_date)

        save_btn.bind(on_release=do_save)
        panel.add_widget(actions)
        popup.open()

    def _confirm_delete(self, edit_popup, event_id):
        edit_popup.dismiss()
        delete_event(event_id)
        self.build_month_grid()
        self.select_date(self.selected_date)