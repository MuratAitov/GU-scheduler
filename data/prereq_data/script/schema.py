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



# -- Создаём таблицу для программ
# CREATE TABLE IF NOT EXISTS program (
#     id SERIAL PRIMARY KEY,
#     name TEXT NOT NULL
# );

# -- Таблица для хранения групп требований
# -- parent_id позволяет иметь иерархию подгрупп
# -- selection_type: 'ALL' или 'MIN'
# CREATE TABLE IF NOT EXISTS requirement_group (
#     id SERIAL PRIMARY KEY,
#     program_id INT REFERENCES program(id) ON DELETE CASCADE,
#     parent_id INT REFERENCES requirement_group(id) ON DELETE CASCADE,
#     name TEXT NOT NULL,
#     selection_type TEXT,
#     required_credits INT
# );

# -- Таблица для связи requirement_group с курсами
# -- В вашем случае курс уже есть в таблице course, где code – PK
# -- Если нужно указывать исключения, можно добавить флаг excluded.
# CREATE TABLE IF NOT EXISTS requirement_course_link (
#     id SERIAL PRIMARY KEY,
#     requirement_group_id INT REFERENCES requirement_group(id) ON DELETE CASCADE,
#     course_code VARCHAR REFERENCES course(code) ON DELETE CASCADE,
#     excluded BOOLEAN DEFAULT FALSE
# );

# -- Если есть требования, выраженные не конкретными курсами, а шаблонами (типа "MATH 3**"),
# -- или "Core: Writing", их можно хранить в дополнительной таблице заметок.
# -- Но для упрощения можно хранить их как "виртуальные курсы" в requirement_course_link,
# -- указывая course_code как несуществующий код, или использовать таблицу notes:
# CREATE TABLE IF NOT EXISTS requirement_notes (
#     id SERIAL PRIMARY KEY,
#     requirement_group_id INT REFERENCES requirement_group(id) ON DELETE CASCADE,
#     note TEXT
# );

# -- Таблица для концентраций
# CREATE TABLE IF NOT EXISTS concentration (
#     id SERIAL PRIMARY KEY,
#     program_id INT REFERENCES program(id) ON DELETE CASCADE,
#     name TEXT NOT NULL,
#     selection_type TEXT,
#     required_credits INT
# );

# -- Аналогично, концентрации могут иметь requirement_group
# -- Либо можно хранить их требования так же, как у program
# -- но для упрощения – сделаем связь концентрации с requirement_group:
# CREATE TABLE IF NOT EXISTS concentration_requirement_link (
#     id SERIAL PRIMARY KEY,
#     concentration_id INT REFERENCES concentration(id) ON DELETE CASCADE,
#     requirement_group_id INT REFERENCES requirement_group(id) ON DELETE CASCADE
# );





# -- Отключаем проверку ссылочной целостности (необязательно)
# -- SET session_replication_role = 'replica';

# -- Удаляем все таблицы, кроме course
# DROP TABLE IF EXISTS concentration_requirement_link CASCADE;
# DROP TABLE IF EXISTS concentration CASCADE;
# DROP TABLE IF EXISTS requirement_course_link CASCADE;
# DROP TABLE IF EXISTS requirement_notes CASCADE;
# DROP TABLE IF EXISTS requirement_group CASCADE;
# DROP TABLE IF EXISTS program CASCADE;

# -- Включаем обратно проверку ссылочной целостности (если отключали)
# -- SET session_replication_role = 'origin';





# CREATE TABLE major (
#     id SERIAL PRIMARY KEY,
#     name TEXT NOT NULL,
#     data JSONB NOT NULL  -- сюда сохраняем JSON c requirement_groups и др.
# );

# CREATE TABLE concentration (
#     id SERIAL PRIMARY KEY,
#     major_id INT REFERENCES major(id) ON DELETE CASCADE,
#     name TEXT NOT NULL,
#     data JSONB NOT NULL  -- сюда сохраняем JSON по концентрациям
# );

# CREATE TABLE minor (
#     id SERIAL PRIMARY KEY,
#     name TEXT NOT NULL,
#     data JSONB NOT NULL
# );
