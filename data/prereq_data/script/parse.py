import requests
from bs4 import BeautifulSoup
import json
import re

url = "https://www.gonzaga.edu/school-of-engineering-applied-science/degrees-and-programs/computer-science/cpsc-courses"

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

courses = []

course_wrappers = soup.find_all('div', class_='course-wrapper')

def parse_prerequisites(text):
    # Удаляем ненужные символы и приводим к стандартному виду
    text = text.replace('\n', ' ').replace('\r', ' ').strip()
    # Рекурсивно парсим строку пререквизитов
    tokens = re.findall(r'\(|\)|\w+|\band\b|\bor\b', text)
    def parse_tokens(tokens):
        result = []
        while tokens:
            token = tokens.pop(0)
            if token == '(':
                sub_expr = parse_tokens(tokens)
                result.append(sub_expr)
            elif token == ')':
                break
            elif token.lower() == 'and' or token.lower() == 'or':
                result.append(token.lower())
            else:
                # Собираем название курса и минимальную оценку
                course = token
                while tokens and tokens[0] not in ('and', 'or', '(', ')'):
                    course += ' ' + tokens.pop(0)
                result.append(course.strip())
        return result
    parsed = parse_tokens(tokens)
    return parsed

for wrapper in course_wrappers:
    course = {}

    # Извлечение названия курса
    title_div = wrapper.find('div', class_='course-subj-num-title')
    if title_div:
        course['name'] = title_div.get_text(strip=True)

    # Извлечение описания
    description_div = wrapper.find('div', class_='course-description')
    if description_div:
        course['description'] = description_div.get_text(strip=True)

    # Извлечение информации о семестре
    if description_div:
        text = description_div.get_text()
        # Поиск терминов в тексте
        terms = []
        if 'Fall' in text:
            terms.append('Fall')
        if 'Spring' in text:
            terms.append('Spring')
        if 'Summer' in text:
            terms.append('Summer')
        course['term'] = ', '.join(terms) if terms else None

    # Извлечение пререквизитов
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
with open('courses.json', 'w', encoding='utf-8') as f:
    json.dump(courses, f, ensure_ascii=False, indent=4)

print("Данные успешно сохранены в 'courses.json'")
