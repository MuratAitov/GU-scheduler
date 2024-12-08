import psycopg2
import json
import networkx as nx
import plotly.graph_objects as go

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.credentials import *

# Функция для подключения к базе данных
def get_connection():
    return psycopg2.connect(
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

# Функция для обработки одного курса
def process_course(graph, course_code, parent=None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT prerequisite_schema FROM prerequisites WHERE course_code = %s", (course_code,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    if not result:
        print(f"No prerequisites found for {course_code}")
        return

    prerequisite_schema = result[0]

    # Добавляем узел для курса
    if parent is None:
        graph.add_node(course_code, label=course_code, data={"type": "root"})  # Корневой узел
    else:
        graph.add_node(course_code, label=course_code, data={"type": "course"})
        graph.add_edge(parent, course_code)  # Связываем с родителем

    # Обрабатываем зависимости
    process_prerequisite(graph, prerequisite_schema, course_code)

# Функция для обработки зависимости
def process_prerequisite(graph, prerequisite_schema, parent):
    if "course" in prerequisite_schema:  # Если это конечный курс
        course = prerequisite_schema["course"]
        graph.add_node(course, label=course, data={"type": "course", "min_grade": prerequisite_schema.get("min_grade", None)})
        graph.add_edge(parent, course)
    elif "type" in prerequisite_schema and "requirements" in prerequisite_schema:  # Если это AND/OR узел
        node_label = f"{parent}_{prerequisite_schema['type']}"  # Создаем уникальный узел для AND/OR
        graph.add_node(node_label, label=prerequisite_schema["type"], data={"type": prerequisite_schema["type"]})
        graph.add_edge(parent, node_label)  # Связываем с родителем
        for req in prerequisite_schema["requirements"]:  # Рекурсивно обрабатываем зависимости
            process_prerequisite(graph, req, node_label)

# Визуализация с Plotly
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
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='Interactive Dependency Graph',
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=40),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False),
                        dragmode='pan'  # Позволяет перетаскивать
                    ))
    fig.show()

# Пример использования
if __name__ == "__main__":
    graph = nx.DiGraph()

    # Обрабатываем один курс (например, CPEN 231)
    course_code = "CPSC 346"  # Замените на нужный курс
    process_course(graph, course_code)

    # Визуализируем дерево зависимостей интерактивно
    visualize_tree_plotly(graph)
