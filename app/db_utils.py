from .credentials import *

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

def add_user_to_db(username, email, password_hash, name):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_name, email, password, name)
                VALUES (%s, %s, %s, %s)
            """, (username, email, password_hash, name))
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


if __name__ == '__main__':
    get_connection()
    print("everythin is ok")