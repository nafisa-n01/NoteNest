# widgets/dashboard_tile.py
# One square feature tile on the home dashboard (Notes / Pomodoro / Reminders).
# Handles its own tap detection (same pattern as widgets/note_card.py) and
# its own theme coloring, since HomeScreen just loops over tiles generically.

from kivymd.uix.card import MDCard
from kivy.properties import StringProperty

from theme.theme_manager import theme_manager
from theme.palettes import CARD_PRIMARY, TEXT_PRIMARY


class DashboardTile(MDCard):
    label = StringProperty("")           # text shown on the tile, e.g. "Notes"
    target_screen = StringProperty("")   # ScreenManager name to switch to on tap

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(on_kv_post=lambda *x: self.apply_theme())

    # ─── colors this tile and its label ───
    def apply_theme(self):
        self.md_bg_color = theme_manager.get_color(CARD_PRIMARY)
        # tile_label is the id given to the MDLabel inside <DashboardTile> in app.kv
        if "tile_label" in self.ids:
            self.ids.tile_label.text_color = theme_manager.get_color(TEXT_PRIMARY)

    # ─── tap detection — MDCard doesn't reliably fire on_release when
    #     nested in some layouts, so track touch start/end manually,
    #     exactly like NoteCard does ───
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_mine = True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and getattr(self, '_touch_mine', False):
            self._touch_mine = False
            from kivymd.app import MDApp
            MDApp.get_running_app().root.current = self.target_screen
            return True
        self._touch_mine = False
        return super().on_touch_up(touch)