import calendar
from datetime import datetime

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from widgets.category_chip import CategoryChip
from widgets.checklist_item import ChecklistItem


try:
    from database.task_queries import (
        get_all_task_dates,
        get_tasks_by_date,
    )
except ImportError:
    from mock_queries import (
        get_all_task_dates,
        get_tasks_by_date,
    )


class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.selected_date = None
        self.active_category = "All"
        self.chips = {}
        self.current_tasks = []

        # Main screen layout
        self.main_layout = BoxLayout(
            orientation="vertical",
            padding=16,
            spacing=10,
        )

        # Cream background
        with self.main_layout.canvas.before:
            Color(0.96, 0.93, 0.86, 1)

            self.bg_rect = Rectangle(
                pos=self.main_layout.pos,
                size=self.main_layout.size,
            )

        self.main_layout.bind(
            pos=self.update_background,
            size=self.update_background,
        )

        # Back button row
        back_row = BoxLayout(
            size_hint_y=None,
            height=40,
        )

        back_btn = Button(
            text="← Home",
            size_hint_x=None,
            width=100,
            background_normal="",
            background_color=(0.24, 0.19, 0.15, 1),
            color=(0.96, 0.93, 0.86, 1),
            font_size=13,
        )

        back_btn.bind(on_press=self.go_back)

        back_row.add_widget(back_btn)
        back_row.add_widget(Label())

        # Category filter chips
        chip_row = BoxLayout(
            orientation="horizontal",
            spacing=8,
            size_hint_y=None,
            height=44,
            padding=[0, 4, 0, 4],
        )

        for category in [
            "All",
            "Study",
            "Life",
            "Health",
            "Work",
        ]:
            chip = CategoryChip(category=category)
            chip.on_select = self.on_chip_selected

            self.chips[category] = chip
            chip_row.add_widget(chip)

        # Select All by default
        self.chips["All"].selected = True
        self.chips["All"].update_style()

        # Month navigation header
        header = BoxLayout(
            size_hint_y=None,
            height=50,
            spacing=10,
        )

        self.prev_btn = Button(
            text="<",
            size_hint_x=None,
            width=40,
            background_normal="",
            background_color=(0.24, 0.19, 0.15, 1),
            color=(0.96, 0.93, 0.86, 1),
            font_size=18,
        )

        self.prev_btn.bind(on_press=self.prev_month)

        self.month_label = Label(
            text="",
            font_size=18,
            bold=True,
            color=(0.02, 0.01, 0.01, 1),
        )

        self.next_btn = Button(
            text=">",
            size_hint_x=None,
            width=40,
            background_normal="",
            background_color=(0.24, 0.19, 0.15, 1),
            color=(0.96, 0.93, 0.86, 1),
            font_size=18,
        )

        self.next_btn.bind(on_press=self.next_month)

        header.add_widget(self.prev_btn)
        header.add_widget(self.month_label)
        header.add_widget(self.next_btn)

        # Day names
        days_header = GridLayout(
            cols=7,
            size_hint_y=None,
            height=30,
        )

        for day_name in [
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun",
        ]:
            days_header.add_widget(
                Label(
                    text=day_name,
                    font_size=12,
                    color=(0.43, 0.41, 0.38, 1),
                    bold=True,
                )
            )

        # Calendar date grid
        self.calendar_grid = GridLayout(
            cols=7,
            size_hint_y=None,
            spacing=4,
        )

        self.calendar_grid.bind(
            minimum_height=self.calendar_grid.setter("height")
        )

        # Selected-date task title
        self.task_label = Label(
            text="Tap a date to see tasks",
            font_size=14,
            color=(0.43, 0.41, 0.38, 1),
            size_hint_y=None,
            height=30,
            halign="left",
            valign="middle",
        )

        self.task_label.bind(
            size=self.task_label.setter("text_size")
        )

        # Task list
        self.task_list = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=8,
        )

        self.task_list.bind(
            minimum_height=self.task_list.setter("height")
        )

        scroll = ScrollView()
        scroll.add_widget(self.task_list)

        # Add widgets to main screen
        self.main_layout.add_widget(back_row)
        self.main_layout.add_widget(chip_row)
        self.main_layout.add_widget(header)
        self.main_layout.add_widget(days_header)
        self.main_layout.add_widget(self.calendar_grid)
        self.main_layout.add_widget(self.task_label)
        self.main_layout.add_widget(scroll)

        self.add_widget(self.main_layout)

        self.build_calendar()

    def update_background(self, instance, value):
        """
        Keep the background rectangle the same size as the layout.
        """

        self.bg_rect.pos = self.main_layout.pos
        self.bg_rect.size = self.main_layout.size

    def go_back(self, instance):
        """
        Return to the Home screen.
        """

        self.manager.current = "home"

    def on_chip_selected(self, category, selected):
        """
        Filter tasks by the selected category.
        """

        for chip_category, chip in self.chips.items():
            if chip_category != category:
                chip.deselect()

        # Keep one category selected
        if not selected:
            self.chips[category].selected = True
            self.chips[category].update_style()
            return

        self.active_category = category

        if self.selected_date:
            self.show_tasks(self.current_tasks)

    def build_calendar(self):
        """
        Build the calendar grid for the current month.
        """

        self.calendar_grid.clear_widgets()

        month_name = datetime(
            self.current_year,
            self.current_month,
            1,
        ).strftime("%B %Y")

        self.month_label.text = month_name

        task_dates = get_all_task_dates()
        month_calendar = calendar.monthcalendar(
            self.current_year,
            self.current_month,
        )

        today = datetime.now()

        for week in month_calendar:
            for day in week:
                if day == 0:
                    self.calendar_grid.add_widget(
                        Label(text="")
                    )
                    continue

                date_str = (
                    f"{self.current_year}-"
                    f"{self.current_month:02d}-"
                    f"{day:02d}"
                )

                has_tasks = date_str in task_dates

                is_today = (
                    day == today.day
                    and self.current_month == today.month
                    and self.current_year == today.year
                )

                if is_today:
                    background_color = (
                        0.24,
                        0.19,
                        0.15,
                        1,
                    )
                    text_color = (
                        0.96,
                        0.93,
                        0.86,
                        1,
                    )

                elif has_tasks:
                    background_color = (
                        0.82,
                        0.78,
                        0.72,
                        1,
                    )
                    text_color = (
                        0.02,
                        0.01,
                        0.01,
                        1,
                    )

                else:
                    background_color = (
                        0.91,
                        0.88,
                        0.86,
                        1,
                    )
                    text_color = (
                        0.02,
                        0.01,
                        0.01,
                        1,
                    )

                date_button = Button(
                    text=str(day),
                    background_normal="",
                    background_color=background_color,
                    color=text_color,
                    font_size=13,
                    size_hint_y=None,
                    height=36,
                )

                date_button.bind(
                    on_press=lambda instance, selected_date=date_str:
                    self.select_date(selected_date)
                )

                self.calendar_grid.add_widget(date_button)

    def select_date(self, date_str):
        """
        Load tasks for the selected date.
        """

        self.selected_date = date_str
        self.current_tasks = get_tasks_by_date(date_str)

        display_date = datetime.strptime(
            date_str,
            "%Y-%m-%d",
        ).strftime("%B %d, %Y")

        self.task_label.text = (
            f"Tasks for {display_date}:"
        )

        self.show_tasks(self.current_tasks)

    def show_tasks(self, tasks):
        """
        Filter and display tasks.

        Each ChecklistItem receives:
        - title
        - category
        - priority
        - due date
        - attachment link
        - subtasks
        """

        self.task_list.clear_widgets()

        if self.active_category == "All":
            filtered_tasks = tasks
        else:
            filtered_tasks = [
                task
                for task in tasks
                if task.get("category")
                == self.active_category
            ]

        if not filtered_tasks:
            self.task_list.add_widget(
                Label(
                    text="No tasks for this category",
                    font_size=13,
                    color=(0.43, 0.41, 0.38, 1),
                    size_hint_y=None,
                    height=36,
                )
            )
            return

        for task in filtered_tasks:
            checklist_item = ChecklistItem(
                text=task.get("title", "Untitled task"),
                checked=task.get("completed", False),
                category=task.get(
                    "category",
                    "Study",
                ),
                priority=task.get(
                    "priority",
                    "Medium",
                ),
                due_date=task.get(
                    "due_date",
                    "",
                ),
                link=task.get(
                    "link",
                    "",
                ),
                subtasks=task.get(
                    "subtasks",
                    [],
                ),
            )

            self.task_list.add_widget(
                checklist_item
            )

    def prev_month(self, instance):
        """
        Move to the previous month.
        """

        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1

        self.build_calendar()

    def next_month(self, instance):
        """
        Move to the next month.
        """

        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1

        self.build_calendar()