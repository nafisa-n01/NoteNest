"""
database/calendar_queries.py

Data access layer for the Calendar feature's reminders/events.

Deliberately independent of `tasks` and `reminders` (which belong to
the Planner/notification features owned by other screens). This file
owns a single table, `calendar_events`, and is the only place that
table is created or queried -- nothing outside the calendar feature
should need to import from here, and this file should never import
from task_queries.py, reminder_queries.py, category_queries.py, etc.

Only `get_connection` is imported from database/db.py (read-only
import -- db.py itself is never modified by this feature).
"""

from database.db import get_connection


def create_calendar_events_table():
    """
    Ensures the calendar_events table exists, and migrates in the
    event_link column for databases created before it existed --
    CREATE TABLE IF NOT EXISTS alone won't add a column to a table
    that's already there, so we check for it explicitly.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT,
            event_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("PRAGMA table_info(calendar_events)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if "event_link" not in existing_columns:
        cursor.execute("ALTER TABLE calendar_events ADD COLUMN event_link TEXT")
    conn.commit()
    conn.close()


def create_event(user_id, title, event_date, event_time=None, event_link=None):
    """
    Adds one reminder/event on a given date. event_time and
    event_link are both optional.
    Returns the new row's id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO calendar_events(user_id, title, event_date, event_time, event_link)
        VALUES(?, ?, ?, ?, ?)
    ''', (user_id, title, event_date, event_time, event_link))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_events_by_date(event_date, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, title, event_date, event_time, event_link, created_at
        FROM calendar_events
        WHERE event_date = ? AND user_id = ?
        ORDER BY
            CASE WHEN event_time IS NULL OR event_time = '' THEN 0 ELSE 1 END,
            event_time ASC
    ''', (event_date, user_id))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def get_all_event_dates(year, month, user_id):
    """
    Returns a set of 'YYYY-MM-DD' strings for every date in the given
    month/year that has at least one reminder, for the given user.
    Used to draw the small dot under a date in the month grid.
    """
    conn = get_connection()
    cursor = conn.cursor()
    month_prefix = f"{year:04d}-{month:02d}-"
    cursor.execute('''
        SELECT DISTINCT event_date
        FROM calendar_events
        WHERE user_id = ? AND event_date LIKE ?
    ''', (user_id, f"{month_prefix}%"))
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

def get_all_events(user_id):
    """
    All calendar events for a user, across every date -- unlike
    get_events_by_date/get_all_event_dates (which are scoped to one
    day or one month for the screen's own display), this returns
    everything. Used by services/backup_builder.py to include
    calendar reminders in a full backup.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, title, event_date, event_time, event_link, created_at
        FROM calendar_events
        WHERE user_id = ?
        ORDER BY event_date ASC, event_time ASC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def get_event_by_id(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, title, event_date, event_time, event_link, created_at
        FROM calendar_events
        WHERE id = ?
    ''', (event_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def update_event(event_id, title, event_time=None, event_link=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE calendar_events
        SET title = ?, event_time = ?, event_link = ?
        WHERE id = ?
    ''', (title, event_time, event_link, event_id))
    conn.commit()
    conn.close()


def delete_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM calendar_events
        WHERE id = ?
    ''', (event_id,))
    conn.commit()
    conn.close()


def _row_to_dict(row):
    return {
        "id": row[0],
        "user_id": row[1],
        "title": row[2],
        "event_date": row[3],
        "event_time": row[4],
        "event_link": row[5],
        "created_at": row[6],
    }