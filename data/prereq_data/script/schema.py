import psycopg2
import pandas as pd
import os

def connect_to_db():
    """Устанавливает соединение с базой данных PostgreSQL."""
    return psycopg2.connect(
        dbname="gu_scheduler",
        user="postgres",
        password="1103",
        host="localhost",
        port="5432"
    )

def create_tables(cursor):
    """Создает таблицы Courses, Sections и Professors."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Courses (
        code TEXT PRIMARY KEY,
        title TEXT,
        credits INTEGER,
        attribute TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sections (
        crn TEXT,
        term TEXT,
        course_code TEXT,
        days TEXT,
        time TEXT,
        capacity INTEGER,
        enrolled INTEGER,
        remaining INTEGER,
        classroom TEXT,
        PRIMARY KEY (crn, term),
        FOREIGN KEY (course_code) REFERENCES Courses (code)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Professors (
        id SERIAL PRIMARY KEY,
        name TEXT,
        difficulty REAL,
        average_grade REAL
    );
    """)


def process_courses_data(sheet_data):
    """Обрабатывает данные для таблицы Courses."""
    courses_data = sheet_data[['Course', 'Credits', 'Attribute']].drop_duplicates()

    # Обработка NaN в Credits
    courses_data['Credits'] = courses_data['Credits'].fillna('0')  # Заменяем NaN на строку '0'

    # Преобразование Credits: берем только первое число
    courses_data['Credits'] = courses_data['Credits'].astype(str).str.split('-').str[0].astype(int)

    # Разделение Course на code, section и title
    courses_data[['code', 'section', 'title']] = courses_data['Course'].str.extract(r'([A-Z]+-\d+)-(\d+)\s+(.+)')
    courses_data = courses_data[['code', 'title', 'Credits', 'Attribute']].rename(
        columns={'Credits': 'credits', 'Attribute': 'attribute'}
    )
    return courses_data
def process_sections_data(sheet_data):
    """Обрабатывает данные для таблицы Sections."""
    sections_data = sheet_data[['CRN', 'Course', 'Days', 'Time', 'Cap', 'Act', 'Rem', 'Instructor', 'Term', 'Classroom']].copy()

    # Разделение Course на course_code, section и title
    sections_data[['course_code', 'section', 'title']] = sections_data['Course'].str.extract(r'([A-Z]+-\d+)-(\d+)\s+(.+)')

    # Переименование колонок
    sections_data = sections_data.rename(columns={
        'CRN': 'crn',
        'Term': 'term',
        'Days': 'days',
        'Time': 'time',
        'Cap': 'capacity',
        'Act': 'enrolled',
        'Rem': 'remaining',
        'Classroom': 'classroom',
        'Instructor': 'instructor'
    })

    # Преобразование CRN в строку
    sections_data['crn'] = sections_data['crn'].astype(str)

    # Fill NaN values with 0 and convert to integer
    for col in ['capacity', 'enrolled', 'remaining']:
        sections_data[col] = sections_data[col].fillna(0).astype(int)

    # Возвращаем нужные столбцы, включая instructor
    return sections_data[['crn', 'term', 'course_code', 'section', 'days', 'time', 'capacity', 'enrolled', 'remaining', 'classroom', 'instructor']]

def process_professors_data(sections_data):
    """Обрабатывает данные для таблицы Professors."""
    if 'instructor' not in sections_data.columns:
        raise KeyError("Столбец 'instructor' отсутствует в данных sections_data")
    professors_data = sections_data[['instructor']].drop_duplicates().rename(columns={'instructor': 'name'})
    return professors_data

def insert_into_courses(cursor, courses_data):
    """Вставляет данные в таблицу Courses."""
    for _, row in courses_data.iterrows():
        cursor.execute("""
        INSERT INTO Courses (code, title, credits, attribute) VALUES (%s, %s, %s, %s)
        ON CONFLICT (code) DO NOTHING;
        """, (row['code'], row['title'], row['credits'], row['attribute']))

def insert_into_sections(cursor, sections_data):
    """Вставляет данные в таблицу Sections."""
    for _, row in sections_data.iterrows():
        cursor.execute("""
        INSERT INTO Sections (crn, term, course_code, days, time, capacity, enrolled, remaining, classroom)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (crn, term) DO NOTHING;
        """, (row['crn'], row['term'], row['course_code'], row['days'], row['time'], row['capacity'], row['enrolled'], row['remaining'], row['classroom']))

def insert_into_professors(cursor, professors_data):
    """Вставляет данные в таблицу Professors."""
    for _, row in professors_data.iterrows():
        cursor.execute("""
        INSERT INTO Professors (name) VALUES (%s)
        ON CONFLICT (name) DO NOTHING;
        """, (row['name'],))

def main():
    # Пути к данным
    base_dir = os.path.dirname(os.path.abspath("data/prereq_data/script/schema.py"))
    data_path = os.path.join(base_dir, "../../official_attribute_data/fall2022.xlsx")

    # Загрузка данных из Excel
    excel_data = pd.ExcelFile(data_path)
    sheet_data = excel_data.parse(sheet_name=0)

    # Обработка данных
    courses_data = process_courses_data(sheet_data)
    sections_data = process_sections_data(sheet_data)
    professors_data = process_professors_data(sections_data)

    # Подключение к базе данных
    conn = connect_to_db()
    cursor = conn.cursor()

    # Создание таблиц
    create_tables(cursor)

    # Вставка данных
    insert_into_courses(cursor, courses_data)
    insert_into_sections(cursor, sections_data)
    insert_into_professors(cursor, professors_data)

    # Завершение транзакции и закрытие соединения
    conn.commit()
    cursor.close()
    conn.close()
    print("Schema created and data populated successfully.")

if __name__ == "__main__":
    main()
