# screens/editor/formatting_toolbar.py
# The bold/italic/undo/align/font toolbar, pulled out as its own
# reusable widget so the SAME instance can be moved between two
# different positions (docked at top for wide screens, floating at
# the bottom for narrow ones) instead of duplicating every button
# twice in app.kv.

from kivymd.uix.card import MDCard
from kivy.properties import BooleanProperty

from theme.theme_manager import theme_manager
from theme.palettes import BACKGROUND, TEXT_PRIMARY


class FormattingToolbar(MDCard):
    is_compact = BooleanProperty(False)

    # NoteEditorScreen's THEME_MAP can't reach into this widget's own
    # self.ids -- it's a separate widget class with its own id
    # namespace, same reason NoteCard/DashboardTile each need their
    # own apply_theme() instead of relying on THEME_MAP. Called from
    # NoteEditorScreen.on_theme_applied() whenever the theme changes.
    def apply_theme(self):
        # Solid background matching the editor's own background color,
        # instead of the previous hardcoded beige literal that never
        # responded to theme changes at all.
        self.md_bg_color = (0.94, 0.93, 0.97, 1)
        self.elevation = 1 if self.is_compact else 0

        # Bonus fix found while wiring this up: every icon button in
        # here has theme_icon_color: "Custom" set in KV but no actual
        # icon_color assigned anywhere -- THEME_MAP can't reach these
        # either, for the same reason as the background. Set here so
        # icons are reliably visible and theme-aware too.
        icon_color = (0.39, 0.33, 0.48, 1)
        for child_id in (
            "undo_button", "redo_button",
            "bold_button", "italic_button", "underline_button",
            "highlight_button", "link_button",
            "align_left_button", "align_center_button", "align_right_button",
            "font_decrease_button", "font_increase_button", "font_cycle_button",
        ):
            button = self.ids.get(child_id)
            if button is not None:
                button.icon_color = icon_color

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.apply_theme()