#https://www.gonzaga.edu/catalogs/current/undergraduate

import requests
from bs4 import BeautifulSoup
import json

def parse_program_requirements(html):
    soup = BeautifulSoup(html, 'html.parser')

    programs = []
    program_id = 1
    req_group_id = 100
    subgroup_id = 101

    # Найти заголовки программы
    start_tag = soup.find('h2', string=lambda x: x and "B.S. in Computer Science" in x)

    if not start_tag:
        return {"error": "Program not found"}

    program_name = start_tag.text.split(":")[0].strip()
    program_credits = int(start_tag.text.split(":")[1].split()[0])
    program = {
        "id": program_id,
        "name": program_name,
        "total_credits": program_credits,
        "requirement_groups": [],
        "concentrations": []
    }

    # Найти группы требований
    current_tag = start_tag.find_next()
    while current_tag:
        # Останов перед списком курсов
        if current_tag.name == 'a' and "Complete Course List" in current_tag.text:
            break

        if current_tag.name == 'h3' and ("I." in current_tag.text or "II." in current_tag.text):
            group_name = current_tag.text.strip()
            group = {
                "id": req_group_id,
                "name": group_name,
                "selection_type": "ALL",  # Default, update based on the context
                "required_credits": None,
                "subgroups": []
            }
            req_group_id += 1

            # Извлечение курсов или подгрупп
            subgroup_tag = current_tag.find_next()
            while subgroup_tag and subgroup_tag.name not in ['h3', 'h2']:
                if subgroup_tag.name == 'tr':
                    # Найти курсы в строках таблицы
                    course_tag = subgroup_tag.find('span', class_='course')
                    if course_tag:
                        course = course_tag.text.strip()
                        group["subgroups"].append({
                            "id": subgroup_id,
                            "name": "Course",
                            "selection_type": "ALL",
                            "courses": [course]
                        })
                        subgroup_id += 1
                subgroup_tag = subgroup_tag.find_next()

            program["requirement_groups"].append(group)

        current_tag = current_tag.find_next()

    programs.append(program)
    return {"programs": programs}

# Функция для загрузки HTML
def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch URL: {url}, status code: {response.status_code}")

# Главная функция
def main():
    url = "https://www.gonzaga.edu/catalogs/current/undergraduate/school-of-engineering-and-applied-science/computer-science--and--computer-science-and-computational-thinking/computer-science"
    html = fetch_html(url)
    result = parse_program_requirements(html)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
