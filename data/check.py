import pandas as pd
import os

# Путь к папке с файлами Excel
folder_path = "data\official_attribute_data"

# Словарь для хранения данных по группам курсов и атрибутов
grouped_courses = {}

# Чтение всех файлов Excel в папке
for file_name in os.listdir(folder_path):
    if file_name.endswith(".xlsx"):
        file_path = os.path.join(folder_path, file_name)
        term = file_name.split(".")[0]  # Используем имя файла как Term (например, fall2024)

        # Чтение файла
        try:
            data = pd.read_excel(file_path)

            # Проверка наличия нужных колонок
            if 'Course' in data.columns and 'Attribute' in data.columns:
                for _, row in data.iterrows():
                    course_full = row['Course']
                    attribute = row['Attribute']

                    # Получаем только базовую часть курса (до идентификатора секции)
                    base_course = course_full.split("-")[0] + "-" + course_full.split("-")[1]

                    # Добавление данных в словарь
                    if base_course not in grouped_courses:
                        grouped_courses[base_course] = {}
                    if course_full not in grouped_courses[base_course]:
                        grouped_courses[base_course][course_full] = set()
                    grouped_courses[base_course][course_full].add((term, attribute))
        except Exception as e:
            print(f"Не удалось прочитать файл {file_name}: {e}")

# Поиск курсов с различными атрибутами
courses_with_differences = {}

for base_course, sections in grouped_courses.items():
    attributes_set = {}
    for section, attributes in sections.items():
        for term, attr in attributes:
            if attr not in attributes_set:
                attributes_set[attr] = []
            attributes_set[attr].append((section, term))

    # Проверка, есть ли различия
    if len(attributes_set) > 1:
        courses_with_differences[base_course] = attributes_set

# Вывод результатов
for base_course, differences in courses_with_differences.items():
    print(f"Курс: {base_course}")
    for attribute, details in differences.items():
        print(f"  Атрибут: {attribute}")
        for section, term in details:
            print(f"    Секция: {section}, Term: {term}")
    print()
