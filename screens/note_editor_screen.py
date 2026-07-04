# screens/note_editor_screen.py
# Create/edit/delete/duplicate a note. Week 3: fake data replaced with
# real database calls from database/notes_queries.py.

from kivymd.uix.screen import MDScreen
from database.notes_queries import (
    get_notes_by_id,
    create_notes,
    update_notes,
    delete_notes,
    duplicate_notes,
)

# Week 3 TEMP: same placeholder as notes_screen.py -- new notes need a
# notebook_id and there's nowhere in the UI yet to pick one.
DEFAULT_NOTEBOOK_ID = 1


class NoteEditorScreen(MDScreen):
    current_note_id = None  # None = new note, a number = editing existing

    def on_enter(self):
        if self.current_note_id is not None:
            self.load_note(self.current_note_id)

    def load_note(self, note_id):
        # get_notes_by_id() returns one tuple, or None if not found
        note = get_notes_by_id(note_id)
        if note is None:
            self.ids.title_field.text = ""
            self.ids.content_field.text = ""
            return

        self.ids.title_field.text = note[2]        # title
        self.ids.content_field.text = note[3] or "" # content

    def save_note(self):
        title = self.ids.title_field.text.strip()
        content = self.ids.content_field.text.strip()

        if not title:
            print("Please add a title")
            # Week 4 maybe: show a real dialog instead of a print
            return

        if self.current_note_id is None:
            create_notes(DEFAULT_NOTEBOOK_ID, title, content)
        else:
            update_notes(self.current_note_id, title, content)

        self.go_back()

    def delete_note(self):
        if self.current_note_id is not None:
            delete_notes(self.current_note_id)
        self.go_back()

    def duplicate_note(self):
        # Heads up: duplicate_notes() in the database duplicates whatever
        # is currently SAVED for this note -- not whatever's typed in the
        # text fields right now. If someone edits the title/content and
        # hits duplicate without saving first, the duplicate will be based
        # on the old saved version, not their edits. Worth deciding if
        # that's the behavior you want, or if duplicate should save first.
        if self.current_note_id is not None:
            duplicate_notes(self.current_note_id)
        self.go_back()

    def go_back(self):
        self.ids.title_field.text = ""
        self.ids.content_field.text = ""
        self.current_note_id = None
        self.manager.current = "notes"