import psycopg2

# === Подключение к базе данных ===
def connect_to_db():
    """Устанавливает соединение с базой данных PostgreSQL."""
    return psycopg2.connect(
        dbname="gu_scheduler",
        user="postgres",
        password="1103",
        host="localhost",
        port="5432"
    )

# === Создание таблиц ===
def create_tables():
    """Создает таблицы в базе данных."""
    commands = [
        """
        CREATE TABLE IF NOT EXISTS course (
            code VARCHAR NOT NULL PRIMARY KEY,
            title VARCHAR,
            difficulty INTEGER DEFAULT 0,
            attributes JSON DEFAULT '{}'::json,
            description TEXT DEFAULT ''::text,
            department TEXT,
            term TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS corequisites (
            course_code VARCHAR NOT NULL,
            corequisite_course_code VARCHAR NOT NULL,
            PRIMARY KEY (course_code, corequisite_course_code),
            FOREIGN KEY (course_code) REFERENCES course(code) ON DELETE CASCADE,
            FOREIGN KEY (corequisite_course_code) REFERENCES course(code) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS equivalents (
            course_code VARCHAR NOT NULL,
            equivalent_course_code VARCHAR NOT NULL,
            term VARCHAR,
            relation VARCHAR,
            PRIMARY KEY (course_code, equivalent_course_code),
            FOREIGN KEY (course_code) REFERENCES course(code) ON DELETE CASCADE,
            FOREIGN KEY (equivalent_course_code) REFERENCES course(code) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS prerequisites (
            course_code VARCHAR NOT NULL,
            prerequisite_schema JSON NOT NULL,
            PRIMARY KEY (course_code),
            FOREIGN KEY (course_code) REFERENCES course(code) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS section (
            crn VARCHAR NOT NULL PRIMARY KEY,
            credits INTEGER,
            days VARCHAR,
            time VARCHAR,
            cap INTEGER,
            instructor VARCHAR,
            classroom VARCHAR,
            attribute VARCHAR,
            term VARCHAR,
            course_code VARCHAR,
            section VARCHAR,
            FOREIGN KEY (course_code) REFERENCES course(code)
        )
        """
    ]

    conn = None
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        cur.close()
        print("Таблицы успешно созданы.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка при создании таблиц: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    create_tables()
