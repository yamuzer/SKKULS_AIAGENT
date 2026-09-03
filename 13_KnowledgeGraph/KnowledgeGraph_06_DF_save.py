import networkx as nx
import pandas as pd

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

NODE_CSV_PATH = DATA_DIR / "nodes.csv"

RELATION_CSV_PATH = DATA_DIR / "relation.csv"

graph = nx.DiGraph()

graph.add_node(
    '철수',
    type='Person',
    age=30
)

graph.add_node(
    '영희',
    type='Person',
    age=28
)

graph.add_node(
    'ABC 회사',
    type='Company'
)

graph.add_node(
    'XYZ 회사',
    type='Company'
)

graph.add_node(
    '서울',
    type='City'
)

graph.add_node(
    '부산',
    type='City'
)

graph.add_node(
    'Python',
    type='Technology'
)

graph.add_node(
    'Java',
    type='Technology'
)



graph.add_edge(
    '철수',
    'ABC 회사',
    relation='WORK_AT'
)

graph.add_edge(
    'ABC 회사',
    '서울',
    relation='LOCATED_IN'
)

graph.add_edge(
    '철수',
    'Python',
    relation='USES'
)


graph.add_edge(
    '영희',
    'XYZ 회사',
    relation='WORKS_AT'
)

graph.add_edge(
    'XYZ 회사',
    '부산',
    relation='LOCATED_IN'
)

graph.add_edge(
    '영희',
    'Java',
    relation='USES'
)

node_rows = []

for node_name, node_data in graph.nodes(data=True):

    row = {
        'id': node_name,
        'type': node_data.get('type', ''),
        'age': node_data.get('age', '')
    }

    node_rows.append(row)


nodes_df = pd.DataFrame(node_rows)
print(nodes_df)


relation_rows = []

for source, target, edge_data in graph.edges(data=True):

    row = {
        'source': source,
        'relation': edge_data.get('relation', ''),
        'target': target
    }

    relation_rows.append(row)


print()
relation_df = pd.DataFrame(relation_rows)
print(relation_df)

nodes_df.to_csv(
    NODE_CSV_PATH,
    index=False,
    encoding='utf-8-sig'
)


relation_df.to_csv(
    RELATION_CSV_PATH,
    index=False,
    encoding='utf-8-sig'
)

print('csv 저장 완료')