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
    print(course_code)
    cursor.execute(
        "INSERT INTO prerequisites (course_code, prerequisite_schema) VALUES (%s, %s) ON CONFLICT (course_code) DO NOTHING",
        (course_code, json.dumps(prerequisites))
    )


def insert_corequisites(cursor, course_code, corequisites):
    """
    Вставляет corequisites в таблицу corequisites.
    """
    print(f"Inserting corequisites for {course_code}: {corequisites}")
    for corequisite in corequisites:
        cursor.execute(
            """
            INSERT INTO corequisites (course_code, corequisite_course_code)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
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
            course_code = " ".join(course.get("name", "").split()[:2])


            # Проверяем, существует ли курс в таблице course
            if not is_course_exist(cursor, course_code):
                print(f"no class {course_code} found" )
                continue

            if "prerequisites" in course:
                print(f"Processing prerequisites for {course_code}: {course['prerequisites']}")
                prerequisites = course["prerequisites"]

                # Убедитесь, что prerequisites преобразуется в корректный формат
                if isinstance(prerequisites, dict):  # Если prerequisites — объект
                    insert_prerequisites(cursor, course_code, prerequisites)
                elif isinstance(prerequisites, list):  # Если prerequisites — список
                    insert_prerequisites(cursor, course_code, {"courses": prerequisites})
                else:
                    print(f"Invalid prerequisites format for {course_code}: {prerequisites}")

            if "corequisites" in course:
                try:
                    print(f"Processing corequisites for {course_code}: {course['corequisites']}")

                    # Если corequisites — это объект, оборачиваем его в список
                    corequisites = course["corequisites"]
                    if isinstance(corequisites, dict):
                        corequisites = [corequisites]

                    # Извлекаем только названия классов из ключа "course"
                    processed_corequisites = [item["course"] for item in corequisites if "course" in item]

                    # Проверяем, существуют ли эти курсы в таблице course
                    valid_corequisites = [cr for cr in processed_corequisites if is_course_exist(cursor, cr)]
                    if not valid_corequisites:
                        print(f"No valid corequisites for {course_code}: {processed_corequisites}")
                        continue

                    # Вставляем только валидные corequisites
                    insert_corequisites(cursor, course_code, valid_corequisites)
                except Exception as e:
                    print(f"Error processing corequisites for {course_code}: {e}")



            if "equivalent" in course:
                try:
                    print(f"Processing equivalents for {course_code}: {course['equivalent']}")

                    equivalents = course["equivalent"].split(", ")
                    for eq in equivalents:
                        # Извлекаем курс
                        course_eq = eq.split(" - ")[0]

                        # Инициализируем переменные
                        term = None
                        relation = None

                        # Проверяем на наличие ключевых слов "since" или "before"
                        if "since" in eq:
                            relation = "since"
                            term = eq.split("since")[-1].strip()
                        elif "before" in eq:
                            relation = "before"
                            term = eq.split("before")[-1].strip()

                        # Проверяем наличие курса в таблице course
                        if is_course_exist(cursor, course_eq):
                            # Вставляем данные в таблицу equivalents
                            cursor.execute(
                                """
                                INSERT INTO equivalents (course_code, equivalent_course_code, term, relation)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (course_code, equivalent_course_code) DO NOTHING
                                """,
                                (course_code, course_eq, term, relation)
                            )
                        else:
                            print(f"Equivalent course {course_eq} not found in table course.")
                except Exception as e:
                    print(f"Error processing equivalents for {course_code}: {e}")



# Основной скрипт
if __name__ == "__main__":
    import os

    # Определяем базовую директорию для JSON-файлов
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Текущая директория скрипта
    json_folder_path = os.path.normpath(os.path.join(script_dir, "../json_data"))


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
