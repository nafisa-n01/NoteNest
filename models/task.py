class Task:
    def __init__(self, id, title, priority, is_completed, due_date, user_id,
                 category_id=None, activity_type="task"):
        self.id = id
        self.title = title
        self.priority = priority
        self.is_completed = is_completed
        self.due_date = due_date
        self.user_id = user_id
        self.category_id = category_id
        self.activity_type = activity_type

    @classmethod
    def from_row(cls, row):
        """
        Builds a Task from a raw sqlite row, in the exact column order
        tasks is created in db.py:
        id, title, priority, is_completed, due_date, user_id,
        category_id, activity_type
        """
        if row is None:
            return None
        return cls(
            id=row[0], title=row[1], priority=row[2], is_completed=row[3],
            due_date=row[4], user_id=row[5], category_id=row[6],
            activity_type=row[7] if len(row) > 7 else "task",
        )