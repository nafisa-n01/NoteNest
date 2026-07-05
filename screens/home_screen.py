# screens/home_screen.py
# Main dashboard screen — shows the app's features as square tiles.
# Tapping a tile switches the ScreenManager to that feature's screen.
# This screen also owns the top toolbar (menu button -> Settings).

# screens/home_screen.py
from kivymd.uix.screen import MDScreen

from theme.theme_manager import theme_manager
from theme.palettes import BACKGROUND, TEXT_PRIMARY

# Not used directly in this file — but importing it here is what registers
# DashboardTile with Kivy's Factory, so app.kv is able to build <DashboardTile>
# tiles below. Without this import, Kivy throws "Unknown class <DashboardTile>".
from widgets.dashboard_tile import DashboardTile


class HomeScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # on_kv_post fires once, right after this screen's KV rule finishes
        # building. Needed because self.ids isn't populated yet in __init__.
        self.bind(on_kv_post=lambda *x: self.apply_theme())

    # ─── runs every time this screen becomes visible ───
    def on_pre_enter(self, *args):
        # Re-color on every visit, not just once at startup. This is what
        # makes a theme change in Settings actually show up back on Home.
        self.apply_theme()

    # ─── colors the toolbar + tells each tile to color itself ───
    def apply_theme(self):
        self.md_bg_color = theme_manager.get_color(BACKGROUND)
        self.ids.home_label.text_color = theme_manager.get_color(TEXT_PRIMARY)
        self.ids.drawer_layout.md_bg_color = theme_manager.get_color(BACKGROUND)
        self.ids.drawer_title.text_color = theme_manager.get_color(TEXT_PRIMARY)
        self.ids.menu_button.icon_color = theme_manager.get_color(TEXT_PRIMARY)

        # Tiles aren't given individual ids, so loop over whatever's
        # inside the tiles row and re-theme each one that supports it.
        for tile in self.ids.tiles_row.children:
            if hasattr(tile, "apply_theme"):
                tile.apply_theme()

    # ─── settings, opened from the toolbar's gear icon ───
    def open_settings(self):
        self.manager.current = "settings"