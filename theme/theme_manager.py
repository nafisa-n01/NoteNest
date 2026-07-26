# ThemeManager is an EventDispatcher, which means it can hold Kivy
# Properties. theme_name is a StringProperty, so any object can
# "subscribe" to it via .bind() and get notified automatically
# whenever the theme changes — no manual refresh loop needed.

import json
import os

from kivy.event import EventDispatcher
from kivy.properties import StringProperty

from theme.palettes import DEFAULT, DARK, CREAM, MATCHA, MONOCHROME
from app_paths import get_app_data_dir

_PALETTES = {
    "default": DEFAULT,
    "dark": DARK,
    "cream": CREAM,
    "matcha": MATCHA,
    "monochrome": MONOCHROME,
}

THEME_PREFS_FILENAME = "theme_prefs.json"


def _theme_prefs_path():
    return os.path.join(get_app_data_dir(), THEME_PREFS_FILENAME)


class ThemeManager(EventDispatcher):

    theme_name = StringProperty("default")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Persist whenever theme_name changes, for ANY reason -- a
        # button press via set_theme(), or load_saved_theme() itself
        # re-writing the same value back. One shared hook guarantees
        # the saved file always matches the live value, rather than
        # relying on every call site to remember to save separately.
        self.bind(theme_name=self._save_theme_name)

    def set_theme(self, name):
        if name in _PALETTES:
            self.theme_name = name

    def load_saved_theme(self):
        """
        Reads the last-saved theme name from disk and applies it.
        Must be called explicitly, after the Kivy App instance exists
        (e.g. as the very first line of App.build()) -- NOT at module
        import time, since get_app_data_dir() needs a running App on
        Android. If nothing was ever saved, or the file is missing or
        corrupted, this silently does nothing and the app just keeps
        the "default" theme it already starts with.
        """
        prefs_path = _theme_prefs_path()
        if not os.path.exists(prefs_path):
            return
        try:
            with open(prefs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        saved_name = data.get("theme_name")
        if saved_name in _PALETTES:
            self.theme_name = saved_name

    def _save_theme_name(self, instance, value):
        try:
            with open(_theme_prefs_path(), "w", encoding="utf-8") as f:
                json.dump({"theme_name": value}, f)
        except OSError:
            # Non-fatal -- worst case, the next launch just falls back
            # to the default theme instead of the last-used one.
            pass

    def set_default_theme(self):
        self.set_theme("default")

    def set_dark_theme(self):
        self.set_theme("dark")

    def set_cream_theme(self):
        self.set_theme("cream")

    def set_matcha_theme(self):
        self.set_theme("matcha")

    def set_monochrome_theme(self):
        self.set_theme("monochrome")

    def get_color(self, token):
        return _PALETTES[self.theme_name].get(token, token)


theme_manager = ThemeManager()