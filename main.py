# main.py
# App entry point. Loads app.kv (your screens: home, notes, note_editor)
# plus each teammate's own kv file separately, so nobody edits the same
# file as anyone else. Then registers every screen with the manager —
# the name="..." string here is what every navigation call in the app
# (tile taps, self.manager.current, go_back()) must match exactly.

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

from screens.home_screen import HomeScreen
from screens.notes_screen import NotesScreen
from screens.note_editor_screen import NoteEditorScreen
from screens.settings_screen import SettingsScreen
from screens.timer_screen import TimerScreen
# NOT importing CalendarScreen yet — Person 3 hasn't sent that file.
# Importing a file that doesn't exist on your machine crashes main.py
# on startup with ModuleNotFoundError. Add this back in once you have it.


class NoteNestApp(MDApp):

    def build(self):
        self.title = "NoteNest"

        Builder.load_file("app.kv")               # home, notes, note_editor
        Builder.load_file("settings_screen.kv")    # Nafisa's layout
        Builder.load_file("timer_screen.kv")       # Nafisa's layout

        sm = ScreenManager()

        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(NotesScreen(name="notes"))
        sm.add_widget(NoteEditorScreen(name="note_editor"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(TimerScreen(name="timer"))

        sm.current = "home"
        return sm


if __name__ == "__main__":
    NoteNestApp().run()