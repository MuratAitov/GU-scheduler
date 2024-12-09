from .credentials import *
from app.credentials import DBNAME, USER, PASSWORD, HOST, PORT
import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

def user_exists(email):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
            return cur.fetchone() is not None
    finally:
        conn.close()

def add_user_to_db(username, email, password_hash, name, major_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_name, email, password, name, major_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, email, password_hash, name, major_id))
        conn.commit()
    finally:
        conn.close()
def get_user_by_email(email):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_name, email, password, name FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if row:
                # row в форме (user_name, email, password_hash, name)
                return {
                    'user_name': row[0],
                    'email': row[1],
                    'password_hash': row[2],
                    'name': row[3]
                }
            return None
    finally:
        conn.close()

def get_all_courses_from_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT code, title FROM course")
            rows = cur.fetchall()
            courses = []
            for r in rows:
                courses.append({
                    "code": r[0],
                    "title": r[1]
                })
            return courses
    finally:
        conn.close()




def get_all_courses_from_db_fro_prereq():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT course_code FROM prerequisites")  # допустим, у вас есть таблица courses
            rows = cur.fetchall()
            # rows будет списком кортежей [(CPSC 121,), (CPSC 122,), ...]
            return [r[0] for r in rows]
    finally:
        conn.close()


def update_user_courses(user_name, courses_data):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for course in courses_data:
                class_taken = course["class_taken"]
                difficulty = course["difficulty"]
                deleted = course.get("deleted", False)

                if deleted:
                    # Удаляем курс из user_courses
                    cur.execute("DELETE FROM user_courses WHERE user_name=%s AND class_taken=%s",
                                (user_name, class_taken))
                else:
                    # Проверяем наличие
                    cur.execute("SELECT 1 FROM user_courses WHERE user_name=%s AND class_taken=%s",
                                (user_name, class_taken))
                    exists = cur.fetchone()
                    if exists:
                        # Обновляем сложность
                        cur.execute("UPDATE user_courses SET difficulty=%s WHERE user_name=%s AND class_taken=%s",
                                    (difficulty, user_name, class_taken))
                    else:
                        # Добавляем новый курс
                        cur.execute("INSERT INTO user_courses (user_name, class_taken, difficulty) VALUES (%s, %s, %s)",
                                    (user_name, class_taken, difficulty))
        conn.commit()
    finally:
        conn.close()

def get_all_user_courses(user_name):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Предположим, что у вас в таблице user_courses есть столбец difficulty
            # Если нет - уберите difficulty из SELECT
            cur.execute("SELECT class_taken, difficulty FROM user_courses WHERE user_name = %s", (user_name,))
            rows = cur.fetchall()
            classes = []
            for r in rows:
                # r[0] - class_taken, r[1] - difficulty
                classes.append({
                    "class_taken": r[0],
                    "difficulty": r[1]
                })
            return classes
    finally:
        conn.close()
        
def get_all_majors():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM majors ORDER BY name")
            return cur.fetchall()
    finally:
        conn.close()

if __name__ == '__main__':
    get_connection()
    print("everythin is ok")