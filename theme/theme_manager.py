# ThemeManager is an EventDispatcher, which means it can hold Kivy
# Properties. theme_name is a StringProperty, so any object can
# "subscribe" to it via .bind() and get notified automatically
# whenever the theme changes — no manual refresh loop needed.

from kivy.event import EventDispatcher
from kivy.properties import StringProperty

from theme.palettes import DEFAULT, DARK, FLORAL, MATCHA, MONOCHROME
from theme.theme_store import save_theme, load_theme

_PALETTES = {
    "default": DEFAULT,
    "dark": DARK,
    "floral": FLORAL,
    "matcha": MATCHA,
    "monochrome": MONOCHROME,
}


class ThemeManager(EventDispatcher):

    theme_name = StringProperty("default")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Persists to SQLite whenever theme_name changes, for any
        # reason -- a button press via set_theme(), or a future
        # programmatic change. One shared hook guarantees the saved
        # value always matches whatever's actually active.
        self.bind(theme_name=self._save_theme_name)

    def set_theme(self, name):
        if name in _PALETTES:
            self.theme_name = name

    def load_saved_theme(self):
        """
        Reads the last-saved theme from the SQLite database and
        applies it. Call this once, after create_tables() has run
        (see main.py), so the database file already exists. If
        nothing was ever saved, or the saved value isn't a known
        theme, this silently does nothing and the app keeps whatever
        theme_name already started with ("default").
        """
        saved_name = load_theme()
        if saved_name in _PALETTES:
            self.theme_name = saved_name

    def _save_theme_name(self, instance, value):
        save_theme(value)

    def set_default_theme(self):
        self.set_theme("default")

    def set_dark_theme(self):
        self.set_theme("dark")

    def set_floral_theme(self):
        self.set_theme("floral")

    def set_matcha_theme(self):
        self.set_theme("matcha")

    def set_monochrome_theme(self):
        self.set_theme("monochrome")

    def get_color(self, token):
        return _PALETTES[self.theme_name].get(token, token)


theme_manager = ThemeManager()