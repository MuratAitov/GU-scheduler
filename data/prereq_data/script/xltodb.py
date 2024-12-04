import os
import psycopg2
import pandas as pd
import sys

# Указываем путь к файлу данных
base_dir = os.path.dirname(os.path.abspath("data/prereq_data/script/schema.py"))
data_path = os.path.join(base_dir, "../../official_attribute_data/summer2024.xlsx")


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
def create_tables(cursor):
    """Создает таблицы course и section, если их еще нет."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course (
            Code VARCHAR PRIMARY KEY,
            Title VARCHAR,
            Difficulty INT DEFAULT 0,
            Attributes JSON DEFAULT '{}',
            Description TEXT DEFAULT ''
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS section (
            CRN VARCHAR PRIMARY KEY,
            Credits INT,
            Days VARCHAR,
            Time VARCHAR,
            Cap INT,
            Instructor VARCHAR,
            Classroom VARCHAR,
            Attribute VARCHAR,
            Term VARCHAR,
            Course_Code VARCHAR,
            Section VARCHAR,
            FOREIGN KEY (Course_Code) REFERENCES course(Code)
        );
    """)


# === Обработка строки Course ===
def process_course(course):
    """Обрабатывает строку Course и возвращает код, секцию и название."""
    parts = course.split(" ", 1)
    course_info = parts[0].split("-")
    code = f"{course_info[0]} {course_info[1]}"
    section = course_info[2]
    title = parts[1] if len(parts) > 1 else "No Title"
    return code, section, title


# === Преобразование Credits ===
def parse_credits(credits):
    """Преобразует Credits в INT или возвращает None, если значение некорректное."""
    if pd.isna(credits) or str(credits).strip() == "":
        print("Encountered empty Credits field. Exiting script.")
        sys.exit(1)
    try:
        if "-" in str(credits):
            return None
        return int(credits)
    except ValueError:
        return None


# === Вставка данных в таблицу course ===
def insert_into_course(cursor, code, title, courses_added):
    """Добавляет запись в таблицу course, если курс еще не добавлен."""
    if code not in courses_added:
        cursor.execute("""
            INSERT INTO course (Code, Title)
            VALUES (%s, %s)
            ON CONFLICT (Code) DO NOTHING;
        """, (code, title))
        courses_added[code] = True


# === Вставка данных в таблицу section ===
def insert_into_section(cursor, row, code, section, credits):
    """Добавляет запись в таблицу section."""
    cursor.execute("""
        INSERT INTO section (CRN, Credits, Days, Time, Cap, Instructor, Classroom, Attribute, Term, Course_Code, Section)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (CRN) DO NOTHING;
    """, (
        row['CRN'],
        credits,
        row['Days'],
        row['Time'],
        row['Cap'],
        row['Instructor'],
        row['Classroom'],
        row['Attribute'],
        row['Term'],
        code,
        section
    ))


# === Основной процесс обработки данных ===
def process_data(sheet_data, cursor):
    """Обрабатывает данные из Excel и вставляет их в базу данных."""
    courses_added = {}

    for _, row in sheet_data.iterrows():
        # Обрабатываем колонку Course
        course = row['Course']
        code, section, title = process_course(course)

        # Преобразуем Credits
        credits = parse_credits(row['Credits'])

        # Вставляем данные в таблицу course
        insert_into_course(cursor, code, title, courses_added)

        # Вставляем данные в таблицу section
        insert_into_section(cursor, row, code, section, credits)

        # Условие остановки скрипта
        if course == "WGST-353-S01 Christian Sexual Ethics":
            print(f"Encountered class '{course}'. Stopping script.")
            return  # Выходим из функции, но не прерываем выполнение всей программы

# === Основная функция ===
def main():
    # Читаем данные из Excel
    sheet_data = pd.read_excel(data_path)

    # Подключаемся к базе данных
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Создаем таблицы
        create_tables(cursor)

        # Обрабатываем данные
        process_data(sheet_data, cursor)

        # Сохраняем изменения
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        # Закрываем соединение
        cursor.close()
        conn.close()


# === Запуск скрипта ===
if __name__ == "__main__":
    main()
