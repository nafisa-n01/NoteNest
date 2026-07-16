# screens/home_screen.py
# Main dashboard screen — shows the app's features as cards.
# Tapping a card switches the ScreenManager to that feature's screen.

from kivymd.uix.screen import MDScreen

from theme.theme_manager import theme_manager
from theme.palettes import BACKGROUND, TEXT_PRIMARY, TEXT_SECONDARY
from theme.themed_screen import ThemedScreenMixin

# Importing DashboardTile registers it with Kivy's Factory.
# Without this, app.kv may throw "Unknown class <DashboardTile>".
from widgets.dashboard_tile import DashboardTile


class HomeScreen(ThemedScreenMixin,MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # on_kv_post runs after the KV layout is built.
        # We need this because self.ids is not ready inside __init__.
        self.bind(on_kv_post=lambda *x: self.apply_theme())

    THEME_MAP = {
        "self":          ("md_bg_color", BACKGROUND),
        "drawer_layout": ("md_bg_color", BACKGROUND),
        "drawer_title":  ("text_color", TEXT_PRIMARY),
        "menu_button":   ("icon_color", TEXT_PRIMARY),
        "home_label":    ("text_color", TEXT_PRIMARY),
        "home_subtitle": ("text_color", TEXT_SECONDARY),
    }

    def on_pre_enter(self, *args):
        self.apply_theme()
    
    #new method added
    def on_theme_applied(self):
        for tile in self.ids.tiles_row.children:
            if hasattr(tile, "apply_theme"):
                tile.apply_theme()


    def open_settings(self):
        """
        Open the Settings screen from the gear button.
        """

        self.manager.current = "settings"