# theme/theme_store.py
# Persists the selected theme in the app's SQLite database. Reuses
# Person 1's existing database.db.get_connection() helper -- her
# database/db.py file is never modified. This module owns a single
# new table, app_settings, created here rather than in her schema
# file, so this stays an addition on our side, not a change to hers.

# NOTE: this table is intentionally NEVER touched by backup/export
# code (services/backup_builder.py, services/manual_export.py).
# Theme preference is local-device UI state, not user content -- it
# should not be included in, or restored from, a notes/calendar
# backup file.

from database.db import get_connection

_THEME_KEY = "theme_name"


def _ensure_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_theme(theme_name):
    _ensure_table()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO app_settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    ''', (_THEME_KEY, theme_name))
    conn.commit()
    conn.close()


def load_theme():
    _ensure_table()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM app_settings WHERE key = ?', (_THEME_KEY,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None