# screens/editor/formatting_toolbar.py
# The bold/italic/undo/align/font toolbar, pulled out as its own
# reusable widget so the SAME instance can be moved between two
# different positions (docked at top for wide screens, floating at
# the bottom for narrow ones) instead of duplicating every button
# twice in app.kv.

from kivymd.uix.card import MDCard
from kivy.properties import BooleanProperty

from theme.theme_manager import theme_manager
from theme.palettes import CARD_SECONDARY, TEXT_PRIMARY

_ICON_BUTTON_IDS = [
    "undo_button", "redo_button",
    "bold_button", "italic_button", "underline_button", "highlight_button", "link_button",
    "align_left_button", "align_center_button", "align_right_button",
    "font_decrease_button", "font_increase_button", "font_cycle_button",
]

class FormattingToolbar(MDCard):
    # Set from Python whenever the toolbar is moved -- the KV rule
    # below uses this to switch between its two visual styles (flat
    # and docked, vs rounded/elevated and floating).
    is_compact = BooleanProperty(False)

    def apply_theme(self):
        if self.is_compact:
            self.md_bg_color = theme_manager.get_color(CARD_SECONDARY)
        else:
            self.md_bg_color = (0, 0, 0, 0)

        icon_color = theme_manager.get_color(TEXT_PRIMARY)
        for button_id in _ICON_BUTTON_IDS:
            button = self.ids.get(button_id)
            if button is not None:
                button.icon_color = icon_color

    def on_is_compact(self, instance, value):
        self.apply_theme()