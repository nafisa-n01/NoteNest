from datetime import datetime
from database.db import get_connection
from database.category_queries import get_all_categories, create_category


def get_or_create_category_id(user_id, category_name):
    """
    calendar_screen.py's Add Task form lets the user pick a category by
    NAME (built-in like "Study", or one they created) -- but tasks
    stores category_id as a real FK. This bridges the two: look up an
    existing category with that name for this user, or create it if
    it's the first time it's actually being used (e.g. a built-in
    category nobody's picked yet).
    """
    if not category_name:
        return None

    for row in get_all_categories(user_id):
        # categories schema: id, name, color, user_id
        if row[1] and row[1].casefold() == category_name.casefold():
            return row[0]

    return create_category(name=category_name, color=None, user_id=user_id)


def create_tasks(title, user_id, priority=None, due_date=None, due_time=None,
                  category=None, category_id=None, link="", carry_forward=False,
                  notify_enabled=False, activity_type="task"):
    """
    category can be passed as a NAME (string, e.g. "Study") -- the usual
    case from calendar_screen.py's popup -- or as category_id directly
    if the caller already has it. If both are given, category_id wins.
    """
    resolved_category_id = category_id
    if resolved_category_id is None and category:
        resolved_category_id = get_or_create_category_id(user_id, category)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks(
            title, user_id, priority, due_date, due_time, category_id,
            link, carry_forward, notify_enabled, activity_type, original_due_date
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        title, user_id, priority, due_date, due_time, resolved_category_id,
        link, int(bool(carry_forward)), int(bool(notify_enabled)),
        activity_type, due_date,
    ))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id


def get_all_tasks(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tasks
        WHERE user_id = ?
        ORDER BY due_date ASC
    ''', (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def get_tasks_by_id(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tasks
        WHERE id=?
    ''', (task_id,))
    task = cursor.fetchone()
    conn.close()
    return task


def get_all_task_dates(year, month, user_id=1):
    """
    Matches calendar_screen.py's call: get_all_task_dates(self.current_year,
    self.current_month). Returns date strings within that month that have
    at least one task, for the month-grid "has tasks" dot.
    """
    month_prefix = f"{year:04d}-{month:02d}-"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT date(due_date)
        FROM tasks
        WHERE user_id=? AND due_date LIKE ?
    ''', (user_id, f"{month_prefix}%"))
    rows = cursor.fetchall()
    conn.close()
    return {r[0] for r in rows}


def get_tasks_by_date(due_date, user_id=1):
    """
    Matches calendar_screen.py's AgendaTaskCard, which reads:
    id, title, completed, category, priority, due_time, link,
    is_carried, notify_enabled from each task dict.

    is_carried is True when the task's current due_date has moved away
    from its original_due_date -- i.e. carry_forward_incomplete_tasks()
    pushed it forward from an earlier day it was actually created for.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tasks.id, tasks.title, tasks.is_completed, tasks.priority,
               tasks.due_date, tasks.due_time, tasks.link,
               tasks.notify_enabled, tasks.original_due_date,
               categories.name
        FROM tasks
        LEFT JOIN categories ON tasks.category_id = categories.id
        WHERE tasks.user_id=? AND tasks.due_date like ?
    ''', (user_id, f"{due_date}%"))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1],
            "completed": bool(r[2]),
            "priority": r[3] or "Medium",
            "due_date": r[4],
            "due_time": r[5] or "",
            "link": r[6] or "",
            "notify_enabled": bool(r[7]),
            "is_carried": bool(r[8]) and r[8] != r[4],
            "category": r[9] or "Study",
        }
        for r in rows
    ]


def set_task_completed(task_id, completed):
    """
    Matches calendar_screen.py's on_task_checked, which needs to set
    completed to either True or False (complete_tasks() only ever set
    it to 1, with no way to un-check).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks SET is_completed=?
        WHERE id=?
    ''', (int(bool(completed)), task_id))
    conn.commit()
    conn.close()


def carry_forward_incomplete_tasks(user_id=1, today_date=None):
    """
    Implements the actual "push incomplete task to next date" feature
    behind the carry_forward toggle. Call this once when the calendar
    screen opens (or once per app launch) -- finds every incomplete
    task with carry_forward=1 whose due_date is before today, and
    rolls its due_date forward to today. original_due_date is left
    untouched, so get_tasks_by_date can still tell it was carried.
    """
    if today_date is None:
        today_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks SET due_date=?
        WHERE user_id=? AND carry_forward=1 AND is_completed=0
          AND due_date < ?
    ''', (today_date, user_id, today_date))
    rolled_count = cursor.rowcount
    conn.commit()
    conn.close()
    return rolled_count


def update_tasks(task_id, title, due_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks SET title=?, due_date=?
        WHERE id=?
    ''', (title, due_date, task_id))
    conn.commit()
    conn.close()


def delete_tasks(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM tasks
        WHERE id=?
    ''', (task_id,))
    conn.commit()
    conn.close()


def search_tasks(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tasks
        WHERE title LIKE ? OR due_date LIKE ?
    ''', (f'%{keyword}%', f'%{keyword}%'))
    results = cursor.fetchall()
    conn.close()
    return results


def set_priority(task_id, priority):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks SET priority=?
        WHERE id=?
    ''', (priority, task_id))
    conn.commit()
    conn.close()


def set_due_date(task_id, due_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks SET due_date=?
        WHERE id=?
    ''', (due_date, task_id))
    conn.commit()
    conn.close()


def complete_tasks(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks SET is_completed=1
        WHERE id=?
    ''', (task_id,))
    conn.commit()
    conn.close()