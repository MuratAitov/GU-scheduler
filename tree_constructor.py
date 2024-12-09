import psycopg2
import json
import networkx as nx
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.credentials import *

def get_connection():
    return psycopg2.connect(
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

def process_course(graph, course_code, parent=None, full_tree=False, visited_courses=None):
    if visited_courses is None:
        visited_courses = set()
    # Если курс уже обработан, не обрабатываем повторно
    if course_code in visited_courses:
        return

    visited_courses.add(course_code)

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT prerequisite_schema FROM prerequisites WHERE course_code = %s", (course_code,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    if not result:
        # Узел добавим даже если нет зависимостей
        if parent is None:
            graph.add_node(course_code, label=course_code, data={"type": "root"})
        else:
            graph.add_node(course_code, label=course_code, data={"type": "course"})
            graph.add_edge(parent, course_code)
        print(f"No prerequisites found for {course_code}")
        return

    prerequisite_schema = result[0]

    # Добавляем узел для курса
    if parent is None:
        graph.add_node(course_code, label=course_code, data={"type": "root"})
    else:
        graph.add_node(course_code, label=course_code, data={"type": "course"})
        graph.add_edge(parent, course_code)

    process_prerequisite(graph, prerequisite_schema, course_code, full_tree, visited_courses)

def process_prerequisite(graph, prerequisite_schema, parent, full_tree, visited_courses):
    if "course" in prerequisite_schema:
        course = prerequisite_schema["course"]
        graph.add_node(course, label=course, data={"type": "course", "min_grade": prerequisite_schema.get("min_grade", None)})
        graph.add_edge(parent, course)

        # Если включён full_tree - рекурсивно обрабатываем
        if full_tree:
            process_course(graph, course, parent=None, full_tree=True, visited_courses=visited_courses)
    elif "type" in prerequisite_schema and "requirements" in prerequisite_schema:
        node_label = f"{parent}_{prerequisite_schema['type']}"
        graph.add_node(node_label, label=prerequisite_schema["type"], data={"type": prerequisite_schema["type"]})
        graph.add_edge(parent, node_label)
        for req in prerequisite_schema["requirements"]:
            process_prerequisite(graph, req, node_label, full_tree, visited_courses)


def visualize_tree_plotly(graph):
    pos = nx.spring_layout(graph)  # Позиционируем узлы
    edge_x = []
    edge_y = []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_text = []
    for node in graph.nodes(data=True):
        x, y = pos[node[0]]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node[1]['label'])

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            size=10,
            color='lightblue',
            line_width=2
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='Interactive Dependency Graph',
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=40),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False),
                        dragmode='pan'
                    ))
    fig.show()

def build_level_structure(graph):
    # Находим корневой узел
    root_nodes = [n for n, d in graph.nodes(data=True) if d.get("data", {}).get("type") == "root"]
    if len(root_nodes) == 0:
        raise ValueError("No root node found in the graph.")
    root = root_nodes[0]

    # BFS для определения уровней
    levels = {}
    queue = [(root, 0)]
    visited = set([root])
    while queue:
        node, level = queue.pop(0)
        if level not in levels:
            levels[level] = []
        levels[level].append(node)

        for child in graph.successors(node):
            if child not in visited:
                visited.add(child)
                queue.append((child, level+1))

    # Формируем структуру для узлов по уровням
    levels_list = []
    for level in sorted(levels.keys()):
        level_nodes = []
        for node in levels[level]:
            data = graph.nodes[node].get("data", {})
            level_nodes.append({
                "id": node,
                "label": graph.nodes[node].get("label", node),
                "data": data
            })
        levels_list.append({"level": level, "nodes": level_nodes})

    # Формируем структуру для рёбер по уровням
    # Уровень ребра равен уровню узла-родителя (from)
    edges_by_level = {}
    for edge in graph.edges():
        parent, child = edge
        parent_level = None
        # Найдём уровень parent
        for lvl, nodes in levels.items():
            if parent in nodes:
                parent_level = lvl
                break
        if parent_level is not None:
            if parent_level not in edges_by_level:
                edges_by_level[parent_level] = []
            edges_by_level[parent_level].append({"from": parent, "to": child})

    edges_list = []
    for level in sorted(edges_by_level.keys()):
        edges_list.append({
            "level": level,
            "edges": edges_by_level[level]
        })

    # Итоговый объект
    result = {
        "levels": levels_list,
        "edges": edges_list
    }
    return result

if __name__ == "__main__":
    graph = nx.DiGraph()
    course_code = "CPSC 346"  # Замените на нужный курс
    full_tree_mode = True

    process_course(graph, course_code, full_tree=full_tree_mode)
    # Если хотите визуализировать локально - раскомментируйте:
    # visualize_tree_plotly(graph)

    # Формируем JSON-структуру для передачи другу
    tree_data = build_level_structure(graph)
    json_output = json.dumps(tree_data, indent=2, ensure_ascii=False)
    print(json_output)
