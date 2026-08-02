# models/calendar_event.py

class CalendarEvent:
    """
    Plain data model for one calendar reminder/event.
    Mirrors the calendar_events table (see database/calendar_queries.py).
    event_time and event_link are optional. is_recurring/completed/
    original_date/missed_days support the "shift forward until done"
    recurring reminder behavior.
    """

    def __init__(
        self,
        id,
        user_id,
        title,
        event_date,
        event_time,
        event_link,
        is_recurring,
        completed,
        original_date,
        missed_days,
        created_at,
    ):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.event_date = event_date
        self.event_time = event_time
        self.event_link = event_link
        self.is_recurring = is_recurring
        self.completed = completed
        self.original_date = original_date
        self.missed_days = missed_days
        self.created_at = created_at

    @classmethod
    def from_dict(cls, data):
        """Builds a CalendarEvent from the dicts returned by calendar_queries.py."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            title=data.get("title"),
            event_date=data.get("event_date"),
            event_time=data.get("event_time"),
            event_link=data.get("event_link"),
            is_recurring=bool(data.get("is_recurring")),
            completed=bool(data.get("completed")),
            original_date=data.get("original_date"),
            missed_days=data.get("missed_days") or 0,
            created_at=data.get("created_at"),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "event_date": self.event_date,
            "event_time": self.event_time,
            "event_link": self.event_link,
            "is_recurring": self.is_recurring,
            "completed": self.completed,
            "original_date": self.original_date,
            "missed_days": self.missed_days,
            "created_at": self.created_at,
        }

    def has_time(self):
        return bool(self.event_time)

    def missed_label(self):
        """'Missed yesterday' / 'Missed N days' -- None if not applicable."""
        if self.completed or not self.missed_days:
            return None
        if self.missed_days == 1:
            return "Missed yesterday"
        return f"Missed {self.missed_days} days"

    def __repr__(self):
        return (
            f"CalendarEvent(id={self.id}, title={self.title!r}, "
            f"date={self.event_date}, time={self.event_time}, "
            f"recurring={self.is_recurring}, completed={self.completed})"
        )