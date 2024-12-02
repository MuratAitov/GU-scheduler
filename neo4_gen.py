from neo4j import GraphDatabase
import json

# Подключение к Neo4j
uri = "neo4j+s://8b4da787.databases.neo4j.io"
driver = GraphDatabase.driver(uri, auth=("neo4j", "credentials/Neo4j-8b4da787-Created-2024-11-12.txt"))

# Загрузка данных из JSON файла
with open('courses.json', 'r', encoding='utf-8') as f:
    courses_data = json.load(f)

# Функция для создания узлов курсов
def create_course_nodes(tx, courses):
    for course in courses:
        tx.run("""
            MERGE (c:Course {name: $name})
            SET c.description = $description,
                c.term = $term
        """, name=course['name'], description=course.get('description'), term=course.get('term'))

# Рекурсивная функция для обработки пререквизитов
def create_prerequisites(tx, course_name, prerequisites):
    if isinstance(prerequisites, list):
        operator = None
        items = []
        i = 0
        while i < len(prerequisites):
            item = prerequisites[i]
            if item == 'and' or item == 'or':
                operator = item.upper()
            else:
                if isinstance(item, list):
                    group_name = f"{course_name}_GROUP_{i}"
                    create_prerequisites(tx, group_name, item)
                    items.append(group_name)
                else:
                    items.append(item)
            i += 1

        if operator:
            # Создаем узел группы
            group_node = f"{course_name}_{operator}_GROUP"
            tx.run("""
                MERGE (g:Group {name: $group_name, type: $operator})
                MERGE (c:Course {name: $course_name})
                MERGE (c)-[:REQUIRES]->(g)
            """, group_name=group_node, operator=operator, course_name=course_name)
            for item in items:
                tx.run("""
                    MERGE (p:Course {name: $prereq_name})
                    MERGE (g:Group {name: $group_name})
                    MERGE (g)-[:HAS_PREREQ]->(p)
                """, prereq_name=item, group_name=group_node)
        else:
            for item in items:
                tx.run("""
                    MERGE (c1:Course {name: $course_name})
                    MERGE (c2:Course {name: $prereq_name})
                    MERGE (c1)-[:REQUIRES]->(c2)
                """, course_name=course_name, prereq_name=item)
    else:
        # Одиночный пререквизит
        tx.run("""
            MERGE (c1:Course {name: $course_name})
            MERGE (c2:Course {name: $prereq_name})
            MERGE (c1)-[:REQUIRES]->(c2)
        """, course_name=course_name, prereq_name=prerequisites)

# Основная функция для загрузки данных в Neo4j
def import_courses():
    with driver.session() as session:
        # Создаем узлы курсов
        session.write_transaction(create_course_nodes, courses_data)

        # Обрабатываем пререквизиты
        for course in courses_data:
            if 'prerequisites' in course:
                session.write_transaction(create_prerequisites, course['name'], course['prerequisites'])

# Запуск импорта
import_courses()
driver.close()
