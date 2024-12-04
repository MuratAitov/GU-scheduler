import requests
from bs4 import BeautifulSoup
import json
import re
# for cs
url = "https://www.gonzaga.edu/school-of-engineering-applied-science/degrees-and-programs/computer-science/cpsc-courses"

#for math
#url = 'https://www.gonzaga.edu/college-of-arts-sciences/departments/mathematics/majors-minors-curriculum/courses'

#for CPEN
#url = 'https://www.gonzaga.edu/school-of-engineering-applied-science/degrees-and-programs/computer-engineering/cpen-courses'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

courses = []

course_wrappers = soup.find_all('div', class_='course-wrapper')

def parse_prerequisites(text):
    text = text.replace('\n', ' ').replace('\r', ' ').strip()
    # Replace commas with spaces for better tokenization
    text = text.replace(',', ' , ')
    # Tokenize the input text
    tokens = []
    for token in re.findall(r'\(|\)|,|and|or|[^\s(),]+', text, re.I):
        tokens.append(token)
    # Normalize tokens
    tokens = [token.lower() if token.lower() in ('and', 'or', '(', ')', ',') else token for token in tokens]

    def parse_expression(tokens):
        left = parse_and_expression(tokens)
        while tokens and tokens[0] == 'or':
            tokens.pop(0)  # Remove 'or'
            right = parse_and_expression(tokens)
            left = {"type": "or", "requirements": [left, right]}
        return left

    def parse_and_expression(tokens):
        left = parse_term(tokens)
        while tokens and tokens[0] == 'and':
            tokens.pop(0)  # Remove 'and'
            right = parse_term(tokens)
            if left.get("type") == "and":
                left["requirements"].append(right)
            else:
                left = {"type": "and", "requirements": [left, right]}
        return left

    def parse_term(tokens):
        if tokens[0] == '(':
            tokens.pop(0)  # Remove '('
            expr = parse_expression(tokens)
            if not tokens or tokens[0] != ')':
                raise ValueError("Expected ')'")
            tokens.pop(0)  # Remove ')'
            return expr
        else:
            # Parse course
            course_parts = []
            while tokens and tokens[0] not in ('and', 'or', '(', ')', ','):
                course_parts.append(tokens.pop(0))
            course = ' '.join(course_parts)
            return {"course": course.strip(), "min_grade": None}

    # Parse the tokens
    try:
        parsed = parse_expression(tokens)
    except Exception as e:
        print(f"Error parsing prerequisites: {e}")
        parsed = None

    return parsed


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