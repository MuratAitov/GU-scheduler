import os
import json
import psycopg2

# Функция для подключения к базе данных
def connect_to_db():
    """Устанавливает соединение с базой данных PostgreSQL."""
    return psycopg2.connect(
        dbname="gu_scheduler",
        user="postgres",
        password="1103",
        host="localhost",
        port="5432"
    )

# Функция для проверки наличия курса в таблице course
def is_course_exist(cursor, course_code):
    cursor.execute("SELECT 1 FROM course WHERE code = %s", (course_code,))
    return cursor.fetchone() is not None

# Функция для вставки данных в таблицу prerequisites
def insert_prerequisites(cursor, course_code, prerequisites):
    cursor.execute(
        "INSERT INTO prerequisites (course_code, prerequisite_schema) VALUES (%s, %s) ON CONFLICT (course_code) DO NOTHING",
        (course_code, json.dumps(prerequisites))
    )

# Функция для вставки данных в таблицу corequisites
def insert_corequisites(cursor, course_code, corequisites):
    for corequisite in corequisites:
        cursor.execute(
            "INSERT INTO corequisites (course_code, corequisite_course_code) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (course_code, corequisite)
        )

# Функция для вставки данных в таблицу equivalents
def insert_equivalents(cursor, course_code, equivalents):
    for equivalent in equivalents:
        cursor.execute(
            "INSERT INTO equivalents (course_code, equivalent_course_code) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (course_code, equivalent)
        )

# Основная функция для обработки JSON-файлов
def process_json_file(file_path, connection):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    with connection.cursor() as cursor:
        for course in data:
            course_code = course.get("name", "").split()[0]  # Извлекаем code (например, "CPSC 122")

            # Проверяем, существует ли курс в таблице course
            if not is_course_exist(cursor, course_code):
                continue

            # Добавляем prerequisites
            if "prerequisites" in course:
                insert_prerequisites(cursor, course_code, course["prerequisites"])

            # Добавляем corequisites
            if "corequisites" in course:
                corequisites = [item["course"] for item in course["corequisites"]]
                insert_corequisites(cursor, course_code, corequisites)

            # Добавляем equivalents
            if "equivalent" in course:
                equivalents = course["equivalent"].split(", ")  # Если список эквивалентов разделён запятыми
                insert_equivalents(cursor, course_code, equivalents)

# Основной скрипт
if __name__ == "__main__":
    import os

    # Определяем базовую директорию для JSON-файлов
    base_dir = os.path.dirname(os.path.abspath("data/prereq_data/script/fill_data.py"))
    json_folder_path = os.path.join(base_dir, "../../data/prereq_data/json_data/")

    # Получаем список всех JSON-файлов в папке json_data
    json_files = [
        os.path.join(json_folder_path, file)
        for file in os.listdir(json_folder_path)
        if file.endswith(".json")
    ]

    connection = connect_to_db()

    try:
        for file_path in json_files:
            print(f"Processing file: {file_path}")
            process_json_file(file_path, connection)

        # Сохраняем изменения
        connection.commit()
        print("Данные успешно импортированы в базу данных.")

    except Exception as e:
        print(f"Ошибка: {e}")
        connection.rollback()

    finally:
        connection.close()
