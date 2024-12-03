import psycopg2
import pandas as pd
import json

# Подключение к базе данных
conn = psycopg2.connect(
    dbname="gu_scheduler",
    user="postgres",
    password="1103",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Создание таблиц
cursor.execute("""
CREATE TABLE IF NOT EXISTS classes (
    id SERIAL PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    description TEXT,
    term VARCHAR(50),
    instructor VARCHAR(255),
    credits INT,
    days VARCHAR(20),
    time VARCHAR(50),
    capacity INT,
    enrolled INT,
    remaining INT,
    classroom VARCHAR(100),
    attributes TEXT,
    equivalent TEXT
);

CREATE TABLE IF NOT EXISTS prereq (
    id SERIAL PRIMARY KEY,
    course_name VARCHAR(255),
    prereq_condition TEXT
);

CREATE TABLE IF NOT EXISTS coreq (
    id SERIAL PRIMARY KEY,
    course_name VARCHAR(255),
    coreq_condition TEXT
);
""")
conn.commit()

# Функция для загрузки JSON
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при загрузке JSON файла {file_path}: {e}")
        return []

# Загрузка данных из JSON
cs_courses = load_json("data/prereq_data/json_data/cs_courses.json")
cpen_courses = load_json("data/prereq_data/json_data/cpen_courses.json")
math_courses = load_json("data/prereq_data/json_data/math_courses.json")

# Объединение всех курсов в один список
all_courses = cs_courses + cpen_courses + math_courses

# Загрузка данных из Excel
try:
    fall2024_data = pd.read_excel("data/official_attribute_data/fall2024.xlsx")
except Exception as e:
    print(f"Ошибка при загрузке Excel файла: {e}")
    fall2024_data = pd.DataFrame()

# Приведение заголовков в Excel к удобному виду
if not fall2024_data.empty:
    fall2024_data.columns = [
        "CRN", "Course", "Credits", "Days", "Time", "Cap", "Act", "Rem",
        "WL_Cap", "WL_Act", "WL_Rem", "XL_Cap", "XL_Act", "XL_Rem",
        "Instructor", "Dates", "Classroom", "Attributes", "Term"
    ]

# Функция для обработки значения Credits
def parse_credits(credits):
    try:
        # Если значение — диапазон, берем минимальное значение
        if "-" in str(credits):
            return int(str(credits).split("-")[0])  # Берем первое значение из диапазона
        # Если это число, просто возвращаем его
        return int(credits)
    except ValueError:
        # Если значение не удалось преобразовать, возвращаем NULL
        return None

# Функция для поиска курса в Excel
def find_course_sections(course_name, excel_data):
    course_code = course_name.split(" ")[0] + "-" + course_name.split(" ")[1]
    return excel_data[excel_data["Course"].str.contains(course_code, na=False)]

# Обработка JSON данных и вставка в базу данных
for course in all_courses:
    name = course["name"]
    description = course.get("description", "")
    term = course.get("term", "")
    equivalent = course.get("equivalent", "")

    # Найти данные курса в Excel
    sections = find_course_sections(name, fall2024_data)

    # Вставка данных в таблицу classes
    for _, section in sections.iterrows():
        credits = parse_credits(section["Credits"])  # Обрабатываем значение Credits
        try:
            cursor.execute("""
                INSERT INTO classes (
                    course_name, description, term, instructor, credits,
                    days, time, capacity, enrolled, remaining, classroom, attributes, equivalent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                name, description, term, section["Instructor"], credits,
                section["Days"], section["Time"], section["Cap"], section["Act"],
                section["Rem"], section["Classroom"], section["Attributes"], equivalent
            ))
        except Exception as e:
            print(f"Ошибка при вставке данных класса {name}: {e}")

    # Вставка данных в таблицу prereq
    if "prerequisites" in course:
        prereq_conditions = json.dumps(course["prerequisites"])
        try:
            cursor.execute("""
                INSERT INTO prereq (course_name, prereq_condition)
                VALUES (%s, %s)
            """, (name, prereq_conditions))
        except Exception as e:
            print(f"Ошибка при вставке данных prereq для курса {name}: {e}")

    # Вставка данных в таблицу coreq
    if "corequisites" in course:
        coreq_conditions = json.dumps(course["corequisites"])
        try:
            cursor.execute("""
                INSERT INTO coreq (course_name, coreq_condition)
                VALUES (%s, %s)
            """, (name, coreq_conditions))
        except Exception as e:
            print(f"Ошибка при вставке данных coreq для курса {name}: {e}")



conn.commit()
cursor.close()
conn.close()

print("Данные успешно обработаны и добавлены в базу данных!")
