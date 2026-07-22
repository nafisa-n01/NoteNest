from database.db import get_connection

def create_category(name,color,user_id):
   conn=get_connection()
   cursor=conn.cursor()  
   cursor.execute('''
      INSERT INTO categories(name,color,user_id)
      VALUES(?,?,?)       
    ''',(name,color,user_id))
   conn.commit()
   category_id = cursor.lastrowid #modified here if it crashes let me know - naf
   conn.close()
   return category_id  #modified here if it crashes let me know - naf
def get_all_categories(user_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    SELECT * FROM categories
    WHERE user_id = ?
    ''', (user_id,))
    categories=cursor.fetchall()
    conn.close()
    return categories
def get_categories_by_id(category_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    SELECT * FROM categories
    WHERE id=?               
    ''',(category_id,))
    category=cursor.fetchone()
    conn.close()
    return category
def update_categories(category_id,name,color):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    UPDATE categories SET name=?, color=?
    WHERE id=?               
    ''',(name,color,category_id))
    conn.commit()
    conn.close()
def delete_categories(category_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    DELETE FROM categories 
    WHERE id=?               
    ''',(category_id,))
    conn.commit()
    conn.close()
def assign_categories_to_notes(note_id,category_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute(''' 
    UPDATE notes SET category_id=?
    WHERE id=?
    ''',(category_id,note_id))
    conn.commit()
    conn.close()

