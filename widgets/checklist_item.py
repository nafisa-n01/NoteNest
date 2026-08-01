# widgets/checklist_item.py
# A single checklist task. Per spec:
# - one tap toggles complete/incomplete
# - optional category and priority (user may set neither, either, or both)
# - an optional due date (empty string = not set, hidden in the UI)
# - optional subtasks, each independently checkable
# implementation and isn't part of what this checklist does.
#
# category/priority are placeholder-set for now (not yet wired to the
# real categories table) -- deliberately simple, per "I want a simple
# version to show and test," to be upgraded later.

import os
from datetime import datetime

from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout


Builder.load_file(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "kv",
        "checklist_item.kv",
    )
)


class SubChecklistItem(BoxLayout):
    """A single subtask row inside a checklist item."""

    text = StringProperty("")
    checked = BooleanProperty(False)

    def toggle(self):
        self.checked = not self.checked


class ChecklistItem(BoxLayout):
    """A single checklist task with optional category, priority, due date, and subtasks."""

    text = StringProperty("")
    checked = BooleanProperty(False)

    # Optional -- empty string means "not set", hidden in the UI.
    category = StringProperty("")
    priority = StringProperty("")
    due_date = StringProperty("")

    # Controls subtask visibility.
    expanded = BooleanProperty(False)

    # Each entry is a dict: {"text": str, "checked": bool}.
    subtasks = ListProperty([])

    # Placeholder category set, not yet wired to the real categories
    # table -- "" (not set) is always the first option when cycling.
    CATEGORY_OPTIONS = ["", "Study", "Life", "Health", "Work"]
    CATEGORY_COLORS = {
        "Study": (0.98, 0.87, 0.85, 1),
        "Life": (0.91, 0.95, 0.87, 1),
        "Health": (0.90, 0.94, 0.98, 1),
        "Work": (0.98, 0.90, 0.90, 1),
    }

    # "" (not set) is always the first option when cycling.
    PRIORITY_OPTIONS = ["", "High", "Medium", "Low"]
    PRIORITY_COLORS = {
        "High": (0.98, 0.92, 0.92, 1),
        "Medium": (0.98, 0.93, 0.85, 1),
        "Low": (0.91, 0.95, 0.87, 1),
    }

    def on_kv_post(self, base_widget):
        self.build_subtasks()

    def on_subtasks(self, instance, value):
        if "subtask_container" in self.ids:
            self.build_subtasks()

    def toggle(self):
        """Toggle the main task between completed and incomplete."""
        self.checked = not self.checked

    def toggle_expand(self):
        """Show or hide the subtask section."""
        self.expanded = not self.expanded

        container = self.ids.subtask_container
        expand_button = self.ids.expand_btn

        if self.expanded:
            container.opacity = 1
            container.height = container.minimum_height
            expand_button.text = "▼"
        else:
            container.opacity = 0
            container.height = 0
            expand_button.text = "►"

    def build_subtasks(self):
        """Create one SubChecklistItem widget per subtask entry."""
        container = self.ids.subtask_container
        container.clear_widgets()

        for index, subtask in enumerate(self.subtasks):
            item = SubChecklistItem(
                text=subtask.get("text", ""),
                checked=subtask.get("checked", False),
            )
            item.bind(
                checked=lambda instance, value, i=index: self._on_subtask_checked(i, value)
            )
            container.add_widget(item)

        if self.expanded:
            container.height = container.minimum_height

    def _on_subtask_checked(self, index, value):
        # ListProperty only notifies bound listeners when the property
        # itself is REASSIGNED, not when an existing list is mutated
        # in place -- so this builds a new list with the one entry
        # updated, rather than editing self.subtasks[index] directly.
        updated = list(self.subtasks)
        updated[index] = {**updated[index], "checked": value}
        self.subtasks = updated

    def add_subtask(self, text):
        """Adds a new, unchecked subtask with the given text."""
        if not text.strip():
            return
        self.subtasks = self.subtasks + [{"text": text.strip(), "checked": False}]

    def cycle_category(self):
        """
        Cycles category through CATEGORY_OPTIONS, including "" (not
        set) -- lets a user clear a category by cycling back to it,
        same as priority below.
        """
        try:
            current_index = self.CATEGORY_OPTIONS.index(self.category)
        except ValueError:
            current_index = 0

        next_index = (current_index + 1) % len(self.CATEGORY_OPTIONS)
        self.category = self.CATEGORY_OPTIONS[next_index]

    def cycle_priority(self):
        """Cycles priority through PRIORITY_OPTIONS, including "" (not set)."""
        try:
            current_index = self.PRIORITY_OPTIONS.index(self.priority)
        except ValueError:
            current_index = 0

        next_index = (current_index + 1) % len(self.PRIORITY_OPTIONS)
        self.priority = self.PRIORITY_OPTIONS[next_index]

    def get_category_color(self):
        """Background color for the current category, or transparent if unset."""
        return self.CATEGORY_COLORS.get(self.category, (0, 0, 0, 0))

    def get_priority_color(self):
        """Background color for the current priority, or transparent if unset."""
        return self.PRIORITY_COLORS.get(self.priority, (0, 0, 0, 0))

    def format_due_date(self, date_value):
        """
        Converts an ISO date like "2026-07-25" into "July 25, 2026".
        Falls back to the raw value if it isn't in that format.
        """
        if not date_value:
            return ""

        try:
            parsed_date = datetime.strptime(date_value, "%Y-%m-%d")
            return parsed_date.strftime("%B %d, %Y")
        except ValueError:
            return date_value