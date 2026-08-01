# models/calendar_event.py

class CalendarEvent:
    """
    Plain data model for one calendar reminder/event.
    Mirrors the calendar_events table (see database/calendar_queries.py).
    event_time is optional -- None means an untimed / all-day reminder.
    """

    def __init__(self, id, user_id, title, event_date, event_time, event_link, created_at):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.event_date = event_date
        self.event_time = event_time
        self.event_link = event_link
        self.created_at = created_at

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            title=data.get("title"),
            event_date=data.get("event_date"),
            event_time=data.get("event_time"),
            event_link=data.get("event_link"),
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
            "created_at": self.created_at,
        }
    
    def has_time(self):
        return bool(self.event_time)

    def __repr__(self):
        return (
            f"CalendarEvent(id={self.id}, title={self.title!r}, "
            f"date={self.event_date}, time={self.event_time})"
        )