from kivymd.uix.label import MDIcon
from kivy.properties import (
    NumericProperty,
    ColorProperty,
)


class HourglassWidget(MDIcon):
    """
    Temporary placeholder widget.

    """

    progress = NumericProperty(0.0)

    glass_color = ColorProperty([1, 1, 1, 1])
    sand_color = ColorProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.icon = "hourglass"

        self.theme_icon_color = "Custom"

        self.icon_size = "90sp"

        self.bind(
            glass_color=self.update_colors,
            sand_color=self.update_colors,
        )

        self.update_colors()

    def update_colors(self, *args):
        self.icon_color = self.sand_color