from database.db import get_connection

def create_tasks(title, user_id, activity_type="task", category_id=None, due_date=None, priority=None):
   conn=get_connection()
   cursor=conn.cursor()
   cursor.execute('''
      INSERT INTO tasks(title,user_id,activity_type,category_id,due_date,priority)
      VALUES(?,?,?,?,?,?)
    ''',(title,user_id,activity_type,category_id,due_date,priority))
   conn.commit()
   task_id = cursor.lastrowid
   conn.close()
   return task_id

def get_all_tasks(user_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    SELECT * FROM tasks
    WHERE user_id = ?
    ORDER BY due_date ASC
    ''', (user_id,))
    tasks=cursor.fetchall()
    conn.close()
    return tasks

def get_tasks_by_id(task_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    SELECT * FROM tasks
    WHERE id=?               
    ''',(task_id,))
    task=cursor.fetchone()
    conn.close()
    return task

def get_tasks_by_date(due_date):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    SELECT * FROM tasks
    WHERE due_date=?               
    ''',(due_date,))
    tasks=cursor.fetchall()
    conn.close()
    return tasks

def get_all_task_dates(user_id=1):
    """
    Bridges the real DB into what calendar_screen.py already expects:
    a collection of date strings the calendar checks membership against
    (`date_str in task_dates`). Used to decide which days get the
    "has tasks" highlight color.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT due_date FROM tasks
        WHERE user_id=? AND due_date IS NOT NULL
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {r[0] for r in rows}

def get_tasks_by_date_for_calendar(due_date, user_id=1):
    """
    Bridges the real DB into the dict shape calendar_screen.show_tasks()
    expects (title/completed/category/priority/due_date/link/subtasks) --
    same job get_tasks_by_date() does, but calendar_screen needs dicts,
    not raw tuples, and needs the category NAME (joined from categories)
    not just category_id.

    NOTE: `link` and `subtasks` aren't modeled in the schema yet --
    left as empty placeholders so ChecklistItem doesn't crash. Add a
    subtasks table later if that feature needs to be real.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tasks.id, tasks.title, tasks.is_completed, tasks.priority,
               tasks.due_date, categories.name
        FROM tasks
        LEFT JOIN categories ON tasks.category_id = categories.id
        WHERE tasks.user_id=? AND tasks.due_date=?
    ''', (user_id, due_date))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1],
            "completed": bool(r[2]),
            "priority": r[3] or "Medium",
            "due_date": r[4],
            "category": r[5] or "Study",
            "link": "",
            "subtasks": [],
        }
        for r in rows
    ]

def update_tasks(task_id,title,due_date):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    UPDATE tasks SET title=?, due_date=?
    WHERE id=?               
    ''',(title,due_date,task_id))
    conn.commit()
    conn.close()
def delete_tasks(task_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    DELETE FROM tasks 
    WHERE id=?               
    ''',(task_id,))
    conn.commit()
    conn.close()
def search_tasks(keyword):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    SELECT * FROM tasks
    WHERE title LIKE ? OR due_date LIKE ?              
    ''',(f'%{keyword}%', f'%{keyword}%'))
    results=cursor.fetchall()
    conn.close()
    return results
def set_priority(task_id,priority):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    UPDATE tasks SET priority=?
    WHERE id=?
    ''',(priority,task_id))
    conn.commit()
    conn.close()
def set_due_date(task_id,due_date):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    UPDATE tasks SET due_date=?
    WHERE id=?
    ''',(due_date,task_id))
    conn.commit()
    conn.close()   
def complete_tasks(task_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    UPDATE tasks SET is_completed=1
    WHERE id=?
    ''',(task_id,))
    conn.commit()
    conn.close()