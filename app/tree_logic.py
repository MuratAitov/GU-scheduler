import psycopg2, json
import networkx as nx
from app.credentials import *


from app.db_utils import get_connection

from app.routes_helpers import process_course, build_level_structure  # Вынесем процессы из кода выше

def build_tree_data(course_code, full_tree_mode=False):
    graph = nx.DiGraph()
    process_course(graph, course_code, full_tree=full_tree_mode)
    tree_data = build_level_structure(graph)
    return tree_data
