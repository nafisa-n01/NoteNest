# services/checklist_store.py
#
# Storage for the checklist feature. Uses the same "own table via the
# shared get_connection() helper" pattern as theme/theme_store.py and
# services/session_history.py -- database/db.py is never modified.
# Tables are created here, on first use, via CREATE TABLE IF NOT EXISTS.
#
# Structure: a "checklist" is a named container (e.g. "Shopping List")
# that carries an optional category and priority. Each checklist has
# its own items, and each item can have sub-items -- items and
# sub-items live in the SAME table (checklist_items), linked via
# parent_id (NULL for a top-level item, the parent item's id for a
# sub-item), same self-referencing design as before, now additionally
# scoped to a checklist via checklist_id.

from database.db import get_connection

_TABLES_CREATED = False


def _ensure_tables():
    global _TABLES_CREATED
    if _TABLES_CREATED:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            category TEXT DEFAULT '',
            priority TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checklist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER REFERENCES checklists(id),
            parent_id INTEGER REFERENCES checklist_items(id),
            text TEXT NOT NULL,
            checked INTEGER DEFAULT 0,
            category TEXT DEFAULT '',
            priority TEXT DEFAULT '',
            due_date TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migrates checklist_id into an existing checklist_items table
    # from before this rework -- CREATE TABLE IF NOT EXISTS alone
    # won't add a column to a table that's already there. category/
    # priority/due_date columns are left in place but unused going
    # forward (cheaper than an SQLite column-drop, same approach the
    # calendar feature uses for its own migrations).
    cursor.execute("PRAGMA table_info(checklist_items)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if "checklist_id" not in existing_columns:
        cursor.execute(
            "ALTER TABLE checklist_items ADD COLUMN checklist_id INTEGER REFERENCES checklists(id)"
        )

    conn.commit()
    conn.close()
    _TABLES_CREATED = True


# ── checklists (the named containers) ──

_PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2, "": 3}


def create_checklist(title, priority="", user_id=1):
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO checklists (user_id, title, priority)
        VALUES (?, ?, ?)
    ''', (user_id, title, priority))
    checklist_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return checklist_id


def get_all_checklists(user_id=1):
    """
    Returns every checklist for a user, sorted so High priority is
    always first, then Medium, then Low, then unset -- the only
    sorting rule this feature has, per spec. Checklists sharing the
    same priority keep most-recently-created first as a secondary,
    stable tiebreaker.
    """
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, title, priority, created_at
        FROM checklists
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    checklists = [_checklist_row_to_dict(row) for row in rows]
    checklists.sort(key=lambda c: _PRIORITY_ORDER.get(c["priority"], 3))
    return checklists


def get_checklist_by_id(checklist_id):
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, title, priority, created_at
        FROM checklists
        WHERE id = ?
    ''', (checklist_id,))
    row = cursor.fetchone()
    conn.close()
    return _checklist_row_to_dict(row) if row else None


def update_checklist(checklist_id, title=None, priority=None):
    _ensure_tables()
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if priority is not None:
        fields.append("priority = ?")
        values.append(priority)
    if not fields:
        return
    values.append(checklist_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        UPDATE checklists SET {", ".join(fields)}
        WHERE id = ?
    ''', values)
    conn.commit()
    conn.close()


def delete_checklist(checklist_id):
    """Deletes a checklist and every item/sub-item that belongs to it."""
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM checklist_items
        WHERE checklist_id = ?
    ''', (checklist_id,))
    cursor.execute('DELETE FROM checklists WHERE id = ?', (checklist_id,))
    conn.commit()
    conn.close()


def get_checklist_item_counts(checklist_id):
    """
    Returns (total_items, checked_items) counting only top-level
    items (not sub-items) -- used by the summary card on the main
    list screen (e.g. "2 items").
    """
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(checked), 0)
        FROM checklist_items
        WHERE checklist_id = ? AND parent_id IS NULL
    ''', (checklist_id,))
    total, checked = cursor.fetchone()
    conn.close()
    return total or 0, checked or 0


# ── checklist items (and sub-items) ──

def _row_to_dict(row):
    return {
        "id": row[0],
        "checklist_id": row[1],
        "parent_id": row[2],
        "text": row[3],
        "checked": bool(row[4]),
        "created_at": row[5],
        "updated_at": row[6],
    }


def _checklist_row_to_dict(row):
    return {
        "id": row[0],
        "user_id": row[1],
        "title": row[2],
        "priority": row[3] or "",
        "created_at": row[4],
    }


def create_checklist_item(checklist_id, text, parent_id=None):
    """
    Creates a new item within a checklist. parent_id=None creates a
    top-level item; pass an existing item's id to create a sub-item
    under it.
    Returns the new item's id.
    """
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO checklist_items (checklist_id, parent_id, text, checked)
        VALUES (?, ?, ?, 0)
    ''', (checklist_id, parent_id, text))
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id


def get_items_by_checklist(checklist_id):
    """Top-level items (parent_id IS NULL) for one checklist, oldest first."""
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, checklist_id, parent_id, text, checked, created_at, updated_at
        FROM checklist_items
        WHERE checklist_id = ? AND parent_id IS NULL
        ORDER BY created_at ASC
    ''', (checklist_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def get_subtasks(parent_id):
    """Returns every sub-item belonging to the given parent item, in creation order."""
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, checklist_id, parent_id, text, checked, created_at, updated_at
        FROM checklist_items
        WHERE parent_id = ?
        ORDER BY created_at ASC
    ''', (parent_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def get_all_items_flat():
    """
    Returns EVERY checklist item (top-level and sub-items alike) in
    one flat list. Intended for the manual export/import backup
    feature -- not used by the screens themselves.
    """
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, checklist_id, parent_id, text, checked, created_at, updated_at
        FROM checklist_items
        ORDER BY id ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def set_checked(item_id, checked):
    """Sets a single item's checked state -- the one-tap toggle."""
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE checklist_items SET checked = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (1 if checked else 0, item_id))
    conn.commit()
    conn.close()


def update_checklist_item_text(item_id, text):
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE checklist_items SET text = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (text, item_id))
    conn.commit()
    conn.close()


def delete_checklist_item(item_id):
    """
    Deletes an item. If it's a top-level item, its sub-items are
    deleted too -- SQLite doesn't cascade automatically here, so it's
    handled explicitly in two statements.
    """
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM checklist_items WHERE parent_id = ?', (item_id,))
    cursor.execute('DELETE FROM checklist_items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()


def clear_all_checklist_data():
    """
    Deletes every checklist and every item/sub-item. Used only by
    manual import -- a restore REPLACES current checklist data with
    the backup's data, same as how notes restore already works.
    """
    _ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM checklist_items')
    cursor.execute('DELETE FROM checklists')
    conn.commit()
    conn.close()