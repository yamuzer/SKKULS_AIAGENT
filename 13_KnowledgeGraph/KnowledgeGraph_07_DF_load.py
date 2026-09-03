import networkx as nx
import pandas as pd

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

NODE_CSV_PATH = DATA_DIR / "nodes.csv"

RELATION_CSV_PATH = DATA_DIR / "relation.csv"


loaded_nodes_df = pd.read_csv(
    NODE_CSV_PATH,
    encoding='utf-8-sig'
)

loaded_relations_df = pd.read_csv(
    RELATION_CSV_PATH,
    encoding='utf-8-sig'
)

loaded_graph = nx.DiGraph()

for row in loaded_nodes_df.to_dict(orient='records'):
    node_id = row['id']
    node_type = row['type']
    age = row['age']

    properties = {
        'type': node_type,
    }

    if pd.notna(age):
        properties['age'] = int(age)

    loaded_graph.add_node(
        node_id,
        **properties
    )


for row in loaded_relations_df.to_dict(orient="records"):
    loaded_graph.add_edge(
        row['source'],
        row['target'],
        relation=row['relation']
    )


print('\n[복원되 Node]')

for node, data in loaded_graph.nodes(data=True):
    print(node, data)

print()

print('\n[복원된 edge]')

for source, target, data in loaded_graph.edges(data=True):
    print(f'{source} -- {data["relation"]} -> {target}')