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
    # Tokenize the text
    tokens = []
    for token in re.findall(r'\(|\)|,|and|or|[^\s(),]+', text, re.I):
        tokens.append(token)
    # Normalize tokens
    tokens = [token.lower() if token.lower() in ('and', 'or', '(', ')', ',') else token for token in tokens]

    index = [0]

    def parse_expression():
        left = parse_and_expression()
        while index[0] < len(tokens) and tokens[index[0]] == 'and':
            op = tokens[index[0]]
            index[0] += 1
            right = parse_and_expression()
            left = {'type': op, 'requirements': [left, right]}
        return left

    def parse_and_expression():
        left = parse_term()
        while index[0] < len(tokens) and tokens[index[0]] == 'or':
            op = tokens[index[0]]
            index[0] += 1
            right = parse_term()
            left = {'type': op, 'requirements': [left, right]}
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
            # Parse course and optional minimum grade
            course_parts = []
            while index[0] < len(tokens) and tokens[index[0]] not in ('and', 'or', '(', ')', ','):
                course_parts.append(tokens[index[0]])
                index[0] += 1
            idx = 0
            course_name = []
            min_grade = None
            while idx < len(course_parts):
                if course_parts[idx].lower() == 'minimum':
                    idx += 1
                    if idx < len(course_parts) and course_parts[idx].lower().startswith('grade'):
                        idx += 1
                        if idx < len(course_parts):
                            min_grade = course_parts[idx]
                            idx += 1
                else:
                    course_name.append(course_parts[idx])
                    idx += 1
            course = ' '.join(course_name).strip()
            return {'course': course, 'min_grade': min_grade}

    parsed = parse_expression()
    return parsed

# Dictionary for term abbreviations
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

# Order terms by length (from most specific to general)
term_keywords = sorted(term_abbreviations.keys(), key=len, reverse=True)

def extract_term(description):
    """Function to extract and abbreviate term"""
    for keyword in term_keywords:
        pattern = re.escape(keyword)
        match = re.search(rf'\b{pattern}\b', description)
        if match:
            return term_abbreviations[keyword]
    return None

for wrapper in course_wrappers:
    course = {}

    # Extract course name
    title_div = wrapper.find('div', class_='course-subj-num-title')
    if title_div:
        course['name'] = title_div.get_text(strip=True)

    # Extract description
    description_div = wrapper.find('div', class_='course-description')
    if description_div:
        description_text = description_div.get_text(strip=True)
        course['description'] = description_text

        # Extract term
        course['term'] = extract_term(description_text)

    # --- Modification Starts Here ---

    # Extract prerequisites from a separate block first
    prereq_div = wrapper.find('div', class_='course-prereqs')
    if prereq_div:
        prereq_text = prereq_div.get_text(strip=True)
        if prereq_text:
            course['prerequisites'] = parse_prerequisites(prereq_text)
    else:
        # If no separate prerequisites block, check for prerequisites in the description
        if description_div:
            description_text = description_div.get_text(strip=True)
            prereq_match = re.search(r'Prerequisite[s]*\(?s?\)?:\s*(.+)', description_text, re.I)
            if prereq_match:
                prereq_text = prereq_match.group(1).strip()
                course['prerequisites'] = parse_prerequisites(prereq_text)

    # --- Modification Ends Here ---

    # Extract corequisites
    coreq_label = wrapper.find('div', class_='course-coreq-label')
    if coreq_label:
        coreq_div = coreq_label.find_next_sibling('div', class_='course-coreqs')
        if coreq_div:
            coreq_text = coreq_div.get_text(strip=True)
            course['corequisites'] = parse_prerequisites(coreq_text)

    # Extract equivalents
    equiv_label = wrapper.find('div', class_='course-equiv-label')
    if equiv_label:
        equiv_div = equiv_label.find_next_sibling('div', class_='course-equivs')
        if equiv_div:
            course['equivalent'] = equiv_div.get_text(strip=True)

    courses.append(course)

# Save data to JSON file
with open('math_courses.json', 'w', encoding='utf-8') as f:
    json.dump(courses, f, ensure_ascii=False, indent=4)

print("Data successfully saved to 'cs_courses.json'")
