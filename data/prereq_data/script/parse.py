import requests
from bs4 import BeautifulSoup
import json
import re
# for cs
#url = "https://www.gonzaga.edu/school-of-engineering-applied-science/degrees-and-programs/computer-science/cpsc-courses"

#for math
url = 'https://www.gonzaga.edu/college-of-arts-sciences/departments/mathematics/majors-minors-curriculum/courses'

#for CPEN
#url = 'https://www.gonzaga.edu/school-of-engineering-applied-science/degrees-and-programs/computer-engineering/cpen-courses'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

courses = []

course_wrappers = soup.find_all('div', class_='course-wrapper')

def parse_prerequisites(text):
    text = text.replace('\n', ' ').replace('\r', ' ').strip()
    tokens = re.findall(r'\(|\)|\w+|\band\b|\bor\b', text)

    def parse_tokens(tokens):
        result = {"type": "and", "requirements": []}
        stack = [result]

        while tokens:
            token = tokens.pop(0)
            if token == '(':
                new_group = {"type": "and", "requirements": []}
                stack[-1]["requirements"].append(new_group)
                stack.append(new_group)
            elif token == ')':
                stack.pop()
            elif token.lower() == 'and' or token.lower() == 'or':
                stack[-1]["type"] = token.lower()
            else:
                # Извлечение курса и минимальной оценки
                course = token
                min_grade = None
                while tokens and tokens[0] not in ('and', 'or', '(', ')'):
                    next_token = tokens.pop(0)
                    if next_token.lower() == "minimum" and tokens and tokens[0].lower() == "grade":
                        tokens.pop(0)  # Удаляем "grade"
                        min_grade = tokens.pop(0)  # Сохраняем оценку
                    else:
                        course += f" {next_token}"

                stack[-1]["requirements"].append({
                    "course": course.strip(),
                    "min_grade": min_grade
                })

        return result

    return parse_tokens(tokens)

# Словарь для сокращений термов
term_abbreviations = {
    'Fall & Spring': 'FS',
    'Fall and Spring': 'FS',
    'On sufficient demand': 'OSD',
    'Spring, odd years': 'SO',
    'Fall, odd years': 'FO',
    'Spring, even years': 'SE',
    'Fall, even years': 'FE',
    'Fall': 'F',
    'Spring': 'S'
}

# Упорядочиваем термы по длине (от самых специфичных к общим)
term_keywords = sorted(term_abbreviations.keys(), key=len, reverse=True)

def extract_term(description):
    """Функция для извлечения и сокращения term"""
    for keyword in term_keywords:
        pattern = re.escape(keyword)
        match = re.search(rf'\b{pattern}\b', description)
        if match:
            return term_abbreviations[keyword]
    return None

for wrapper in course_wrappers:
    course = {}

    # Извлечение названия курса
    title_div = wrapper.find('div', class_='course-subj-num-title')
    if title_div:
        course['name'] = title_div.get_text(strip=True)

    # Извлечение описания
    description_div = wrapper.find('div', class_='course-description')
    if description_div:
        description_text = description_div.get_text(strip=True)
        course['description'] = description_text

        # Извлечение term
        course['term'] = extract_term(description_text)

        # Проверяем пререквизиты в описании
        if 'Prerequisite:' in description_text and 'prerequisites' not in course:
            prereq_start = description_text.find('Prerequisite:') + len('Prerequisite:')
            prereq_text = description_text[prereq_start:].strip()
            course['prerequisites'] = parse_prerequisites(prereq_text)
        elif 'Prerequisites:' in description_text and 'prerequisites' not in course:
            prereq_start = description_text.find('Prerequisites:') + len('Prerequisites:')
            prereq_text = description_text[prereq_start:].strip()
            course['prerequisites'] = parse_prerequisites(prereq_text)

    # Извлечение пререквизитов из отдельного блока
    prereq_label = wrapper.find('div', class_='course-prereq-label')
    if prereq_label:
        prereq_div = prereq_label.find_next_sibling('div', class_='course-prereqs')
        if prereq_div:
            prereq_text = prereq_div.get_text(strip=True)
            course['prerequisites'] = parse_prerequisites(prereq_text)

    # Извлечение кореквизитов
    coreq_label = wrapper.find('div', class_='course-coreq-label')
    if coreq_label:
        coreq_div = coreq_label.find_next_sibling('div', class_='course-coreqs')
        if coreq_div:
            coreq_text = coreq_div.get_text(strip=True)
            course['corequisites'] = parse_prerequisites(coreq_text)

    # Извлечение эквивалентов
    equiv_label = wrapper.find('div', class_='course-equiv-label')
    if equiv_label:
        equiv_div = equiv_label.find_next_sibling('div', class_='course-equivs')
        if equiv_div:
            course['equivalent'] = equiv_div.get_text(strip=True)

    courses.append(course)

# Сохранение данных в JSON файл
with open('math_courses.json', 'w', encoding='utf-8') as f:
    json.dump(courses, f, ensure_ascii=False, indent=4)

print("Данные успешно сохранены в 'cs_courses.json'")