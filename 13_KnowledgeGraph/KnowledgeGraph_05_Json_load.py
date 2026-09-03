import networkx as nx
import json

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

JSON_PATH = DATA_DIR / "knowledge_graph.json"

with open(
    JSON_PATH,
    'r',
    encoding='utf-8'
) as file:
    loaded_data = json.load(file)

loaded_graph = nx.DiGraph()

for node in loaded_data['nodes']:
    node_id = node['id']
    properties = {
        key: value
        for key, value in node.items()
        if key != 'id'
    }

    loaded_graph.add_node(
        node_id,
        **properties
    )


for edge in loaded_data['edges']:
    source = edge['source']
    target = edge['target']

    properties = {
        key: value
        for key, value in edge.items()
        if key not in [
            'source',
            'target'
        ]
    }

    loaded_graph.add_edge(
        source,
        target,
        **properties
    )


print('\n[복원되 Node]')

for node, data in loaded_graph.nodes(data=True):
    print(node, data)

print()

print('\n[복원된 edge]')

for source, target, data in loaded_graph.edges(data=True):
    print(f'{source} -- {data["relation"]} -> {target}')