# one note card widget (used by home_screen)
# widgets/note_card.py

from kivymd.uix.card import MDCard
from kivy.properties import StringProperty, NumericProperty, BooleanProperty


class NoteCard(MDCard):
    title = StringProperty("Untitled")
    preview = StringProperty("")
    note_id = NumericProperty(0)
    is_pinned = BooleanProperty(False)
    last_edited = StringProperty("")

    # track that the touch started on this card
    def on_touch_down(self, touch):
        # If the touch landed on the pin icon, let it handle itself --
        # don't record this as "the card was pressed," or the pin
        # button's own tap-to-toggle would also open the note editor.
        if "pin_icon" in self.ids and self.ids.pin_icon.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if self.collide_point(*touch.pos):
            self._touch_mine = True
        return super().on_touch_down(touch)

    # only open note if the tap both started and ended on this card
    def on_touch_up(self, touch):
        # Same exclusion as above -- if this touch is over the pin icon,
        # don't treat it as "open the note," just let the button's own
        # on_release logic run normally.
        if "pin_icon" in self.ids and self.ids.pin_icon.collide_point(*touch.pos):
            self._touch_mine = False
            return super().on_touch_up(touch)

        if self.collide_point(*touch.pos) and getattr(self, '_touch_mine', False):
            self._touch_mine = False
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            editor = app.root.get_screen("note_editor")
            editor.current_note_id = self.note_id
            app.root.current = "note_editor"
            return True
        self._touch_mine = False
        return super().on_touch_up(touch)

    # called when the pin icon is tapped -- hands off to the notes
    # screen, which owns the actual database call and list refresh
    def toggle_pin(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        notes_screen = app.root.get_screen("notes")
        notes_screen.toggle_pin_note(self.note_id, self.is_pinned)