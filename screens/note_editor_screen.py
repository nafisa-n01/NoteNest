# screens/note_editor_screen.py
import os
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock                              
from plyer import filechooser
from widgets.attachment_thumbnail import AttachmentThumbnail
from kivy.metrics import dp

# Registers AttachmentThumbnail with Kivy's Factory, same reason as the
# DashboardTile import earlier — without this, app.kv can't build
# <AttachmentThumbnail>, and you'd get "Unknown class" again.
from widgets.attachment_thumbnail import AttachmentThumbnail

from database.notes_queries import (
    get_notes_by_id,
    create_notes,
    update_notes,
    delete_notes,
    duplicate_notes,
)
from database.attachment_queries import (
    create_attachment,
    get_all_attachments,   # matches Tabshira's actual function name
    delete_attachment,
)

DEFAULT_NOTEBOOK_ID = 1


class NoteEditorScreen(MDScreen):
    current_note_id = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Attachments for the note currently open. Each entry:
        # {"id": <db id, or None if not saved yet>, "path": "local/file.jpg"}
        self.attachments = []

    def on_enter(self):
        self.attachments = []
        if self.current_note_id is not None:
            self.load_note(self.current_note_id)
        self.refresh_attachment_previews()

    def load_note(self, note_id):
        note = get_notes_by_id(note_id)
        if note is None:
            self.ids.title_field.text = ""
            self.ids.content_field.text = ""
            return

        self.ids.title_field.text = note[2]
        self.ids.content_field.text = note[3] or ""

        # attachments table shape from db.py: (id, note_id, file_path, created_at)
        rows = get_all_attachments(note_id)
        self.attachments = [{"id": row[0], "path": row[2]} for row in rows]

    # ─── opens the native file picker, filtered to image files ───
    def pick_image(self):
        if self.current_note_id is None:
            # No note_id yet for a brand-new, unsaved note -- nowhere to
            # attach the photo to in the database. Save the note first.
            print("Save the note before attaching photos")
            # Week 4: replace with a real popup/snackbar instead of print
            return

        # Windows' native file dialog silently changes the app's working
        # directory to match whatever folder you picked a file from. Since
        # the database connects with a relative path, that breaks every
        # query made afterward. Save the current directory here, then
        # restore it once the picker closes.
        self._cwd_before_picker = os.getcwd()

        filechooser.open_file(
            on_selection=self.on_image_selected,
            filters=[["Images", "*.png", "*.jpg", "*.jpeg"]],
        )

    def on_image_selected(self, selection):
        # The file picker's callback can fire on a different thread than
        # the rest of the app (especially on Windows). Touching widgets
        # directly here can silently crash the whole app -- so instead,
        # schedule the actual work to run on Kivy's main thread.
        os.chdir(self._cwd_before_picker)   # undo Windows' directory change
        Clock.schedule_once(lambda dt: self._add_attachment(selection))

    def _add_attachment(self, selection):
        if not selection:
            return  # user cancelled the picker
        self.attachments.append({"id": None, "path": selection[0]})
        self.refresh_attachment_previews()

    # ─── rebuilds the thumbnail row to match self.attachments ───
    def refresh_attachment_previews(self):
        self.ids.attachments_row.clear_widgets()
        for attachment in self.attachments:
            thumb = AttachmentThumbnail(image_path=attachment["path"])
            thumb.attachment_data = attachment
            thumb.bind(on_remove=self.remove_attachment)
            self.ids.attachments_row.add_widget(thumb)
        
        # collapse the whole row to nothing when there are no photos,
        # instead of leaving an empty gap on screen
        self.ids.attachments_scroll.height = dp(88) if self.attachments else 0

    def remove_attachment(self, thumbnail_widget):
        attachment = thumbnail_widget.attachment_data
        if attachment["id"] is not None:
            delete_attachment(attachment["id"])  # only saved attachments need db deletion
        self.attachments.remove(attachment)
        self.refresh_attachment_previews()

    def save_note(self):
        title = self.ids.title_field.text.strip()
        content = self.ids.content_field.text.strip()

        if not title:
            print("Please add a title")
            return

        if self.current_note_id is None:
            create_notes(DEFAULT_NOTEBOOK_ID, title, content)
            # Any photos picked before this first save are lost -- but
            # pick_image() blocks that case above, so it shouldn't happen.
        else:
            update_notes(self.current_note_id, title, content)
            for attachment in self.attachments:
                if attachment["id"] is None:  # newly picked, not saved yet
                    create_attachment(self.current_note_id, attachment["path"])

        self.go_back()

    def delete_note(self):
        if self.current_note_id is not None:
            delete_notes(self.current_note_id)
        self.go_back()

    def duplicate_note(self):
        if self.current_note_id is not None:
            duplicate_notes(self.current_note_id)
        self.go_back()

    def go_back(self):
        self.ids.title_field.text = ""
        self.ids.content_field.text = ""
        self.current_note_id = None
        self.attachments = []
        self.manager.current = "notes"