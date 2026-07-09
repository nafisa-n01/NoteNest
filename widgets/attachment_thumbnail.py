# widgets/attachment_thumbnail.py
# A small square photo preview with a delete "x" in the corner.
# Shown in a row inside the note editor for each attached photo.

from kivymd.uix.floatlayout import MDFloatLayout
from kivy.properties import StringProperty, ObjectProperty


class AttachmentThumbnail(MDFloatLayout):
    image_path = StringProperty("")         # local file path shown in the preview
    attachment_data = ObjectProperty(None)  # dict set by NoteEditorScreen after creation

    # Declares a custom event so NoteEditorScreen can listen for taps on
    # the "x" button without this widget needing to know who's listening
    __events__ = ("on_remove",)

    def on_remove(self, *args):
        pass  # default does nothing; NoteEditorScreen binds its own handler

    def request_remove(self):
        self.dispatch("on_remove")