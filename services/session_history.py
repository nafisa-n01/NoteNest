# services/session_history.py
#
# Read-only query for "every pomodoro session started today" -- used
# by the Timer screen's session history popup. Lives here rather than
# in database/pomodoro_queries.py

from datetime import datetime
from database.db import get_connection


def get_sessions_for_today():
    """
    Returns every pomodoro_sessions row whose started_at falls on
    today's date, most recent first, as a list of
    (id, started_at, completed, duration) tuples.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, started_at, completed, duration
        FROM pomodoro_sessions
        WHERE date(started_at) = ?
        ORDER BY started_at DESC
    ''', (today_str,))
    sessions = cursor.fetchall()
    conn.close()
    return sessions