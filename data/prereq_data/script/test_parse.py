import requests
from bs4 import BeautifulSoup
import re
import json

# Базовый URL
base_url = "https://www.gonzaga.edu/catalogs/current/undergraduate/college-of-arts-and-sciences/"

# Массив с последними частями ссылок
endpoints = [
    "art",
    "biology",
    "broadcast-and-electronic-media-studies",
    "catholic-studies",
    "chemistry_and_biochemistry",
    "classical-civilizations",
    "communication-studies",
    "criminology",
    "dance",
    "english",
    "environmental-studies-and-sciences",
    "film-studies",
    "french",
    "german",
    "health-equity",
    "history",
    "integrated-media",
    "interdisciplinary-arts",
    "international-studies",
    "italian",
    "italian-studies",
    "journalism",
    "mathematics",
    "modern-languages",
    "music",
    "native-american-studies",
    "neuroscience",
    "philosophy",
    "physics",
    "political-science",
    "psychology",
    "public-relations",
    "religious-studies",
    "sociology",
    "solidarity_and_social_justice",
    "spanish",
    "theatre-and-dance",
    "visual-literacy",
    "women-gender-and-sexuality-studies"
]


# Функция для обработки каждой ссылки
def process_endpoint(endpoint):
    url = f"{base_url}{endpoint}"  # Формируем полный URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Поиск содержимого между "Complete Course List" и "University Core"
    html_content = soup.prettify()
    start_marker = "Complete Course List -"
    end_marker = "University Core"

    # Найдём слово после "Complete Course List -"
    start_index = html_content.find(start_marker)
    if start_index != -1:
        start_index += len(start_marker)
        text_after_marker = html_content[start_index:].strip()
        first_word = text_after_marker.split()[0]  # Первое слово после маркера
    else:
        first_word = endpoint  # Если маркер не найден, используем название раздела

    # Создание списка курсов
    courses = []
    course_wrappers = soup.find_all('div', class_='course-wrapper')

    # Словарь для сокращений терминов
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

    # Упорядочиваем ключевые слова по длине
    term_keywords = sorted(term_abbreviations.keys(), key=len, reverse=True)

    def parse_prerequisites(text):
        """Функция для парсинга prerequisites"""
        text = text.replace('\n', ' ').replace('\r', ' ').strip()
        tokens = re.findall(r'\(|\)|,|and|or|[^\s(),]+', text, re.I)
        tokens = [token.lower() if token.lower() in ('and', 'or', '(', ')', ',') else token for token in tokens]
        index = [0]

        def parse_expression():
            left = parse_and_expression()
            while index[0] < len(tokens) and tokens[index[0]] == 'and':
                index[0] += 1
                right = parse_and_expression()
                left = {'type': 'and', 'requirements': [left, right]}
            return left

        def parse_and_expression():
            left = parse_term()
            while index[0] < len(tokens) and tokens[index[0]] == 'or':
                index[0] += 1
                right = parse_term()
                left = {'type': 'or', 'requirements': [left, right]}
            return left

        def parse_term():
            if tokens[index[0]] == '(':
                index[0] += 1
                expr = parse_expression()
                if index[0] >= len(tokens) or tokens[index[0]] != ')':
                    raise ValueError("Expected ')'")
                index[0] += 1
                return expr
            else:
                course_parts = []
                while index[0] < len(tokens) and tokens[index[0]] not in ('and', 'or', '(', ')', ','):
                    course_parts.append(tokens[index[0]])
                    index[0] += 1
                course_name = " ".join(course_parts).strip()
                return {'course': course_name}

        return parse_expression()

    def extract_term(description):
        """Функция для извлечения и сокращения терминов"""
        for keyword in term_keywords:
            pattern = re.escape(keyword)
            match = re.search(rf'\b{pattern}\b', description)
            if match:
                return term_abbreviations[keyword]
        return None

    # Парсинг курсов
    for wrapper in course_wrappers:
        course = {}

        # Название курса
        title_div = wrapper.find('div', class_='course-subj-num-title')
        if title_div:
            course['name'] = title_div.get_text(strip=True)

        # Описание курса
        description_div = wrapper.find('div', class_='course-description')
        if description_div:
            description_text = description_div.get_text(strip=True)
            course['description'] = description_text
            course['term'] = extract_term(description_text)

        # Пререквизиты
        prereq_div = wrapper.find('div', class_='course-prereqs')
        if prereq_div:
            prereq_text = prereq_div.get_text(strip=True)
            course['prerequisites'] = parse_prerequisites(prereq_text)

        # Добавляем курс в список
        courses.append(course)

    # Сохраняем данные в JSON-файл с именем, основанным на first_word
    file_name = f"prereq/{first_word}.json"
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)

    print(f"Data successfully saved to '{file_name}'")

# Обработка всех ссылок
for endpoint in endpoints:
    print(f"Processing: {endpoint}")
    process_endpoint(endpoint)
