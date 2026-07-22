from database.db import get_connection

def create_tasks(title,user_id):
   conn=get_connection()
   cursor=conn.cursor()  
   cursor.execute('''
      INSERT INTO tasks(title,user_id)
      VALUES(?,?)       
    ''',(title,user_id))
   conn.commit()
   task_id = cursor.lastrowid #modified here if it crashes let me know - naf
   conn.close()
   return task_id #modified here if it crashes let me know - naf
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