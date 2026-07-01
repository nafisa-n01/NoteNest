from kivymd.uix.screen import MDScreen
from theme.theme_manager import theme_manager
from kivy.app import App

from theme.palettes import (
    BACKGROUND,
    CARD_PRIMARY,
    CARD_SECONDARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BUTTON,
    BUTTON_TEXT,
    BORDER,
    ACCENT,
)

class SettingsScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bind(on_kv_post=lambda *x: self.apply_theme())

    #appearance settings
    def set_light_theme(self):
        theme_manager.set_light_theme()
        self.refresh_all_screens()

    def set_dark_theme(self):
        theme_manager.set_dark_theme()
        self.refresh_all_screens()

    def set_pink_theme(self):
        theme_manager.set_pink_theme()
        self.refresh_all_screens()

    def set_cyberpunk_theme(self):
        theme_manager.set_cyberpunk_theme()
        self.refresh_all_screens()

    def apply_theme(self):

        self.md_bg_color = theme_manager.get_color(BACKGROUND)

        self.ids.title_label.text_color = theme_manager.get_color(TEXT_PRIMARY)

        self.ids.subtitle_label.text_color = theme_manager.get_color(TEXT_SECONDARY)

        self.ids.appearance_card.md_bg_color = theme_manager.get_color(CARD_PRIMARY)

        self.ids.account_card.md_bg_color = theme_manager.get_color(CARD_SECONDARY)

        self.ids.notification_card.md_bg_color = theme_manager.get_color(CARD_PRIMARY)

        self.ids.about_card.md_bg_color = theme_manager.get_color(CARD_SECONDARY)

        button_color = theme_manager.get_color(BUTTON)

        self.ids.light_button.md_bg_color = button_color
        self.ids.dark_button.md_bg_color = button_color
        self.ids.pink_button.md_bg_color = button_color
        self.ids.cyber_button.md_bg_color = button_color

    #account settings
    def update_account(self):
        pass

    def logout(self):
        pass

    #notification settings
    def toggle_notifications(self):
        pass

    #navigation settings
    def go_back(self):
        App.get_running_app().root.current = "home"

    # Future implementation (after Firebase setup)
    #
    # def login(self):
    #     pass
    #
    # def signup(self):
    #     pass

    def refresh_all_screens(self):

        app = App.get_running_app()

        for screen in app.root.screens:
            if hasattr(screen, "apply_theme"):
                screen.apply_theme()
