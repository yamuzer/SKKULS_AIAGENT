import networkx as nx
import json
from pathlib import Path



BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

JSON_PATH = DATA_DIR / "knowledge_graph.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


graph = nx.DiGraph()

# 철수 ->  ABC 
graph.add_node(
    '철수',
    type='Person',
)
graph.add_node(
    '영희',
    type='Person',
)
graph.add_node(
    'ABC 회사',
    type='Company',
)
graph.add_node(
    '서울',
    type='City',
)

graph.add_node(
    'Python',
    type='Technology',
)

graph.add_node(
    '데이터 분석',
    type='Field',
)



# 실제 관계 종류를 저장한다.
graph.add_edge(
    '철수',
    'ABC 회사',
    relation = 'WORK_AT'
)

graph.add_edge(
    'ABC 회사',
    '서울',
    relation = 'LOCATED_IN'
)

graph.add_edge(
    '철수',
    'Python',
    relation = 'USES'
)


graph.add_edge(
    'Python',
    '데이터 분석',
    relation = 'USED_FOR'
)

graph.add_edge(
    '영희',
    'ABC 회사',
    relation = 'CEO_OF'
)



nodes = []
for node_name, node_data in graph.nodes(data=True):
    node = {
        'id': node_name,
        **node_data
    }
    nodes.append(node)


edges = []

for source, target, edge_data in graph.edges(data=True):
    edge = {
        'source' : source,
        'target': target,
        **edge_data
    }
    edges.append(edge)

graph_data = {
    'nodes':nodes,
    'edges':edges
}


with open(JSON_PATH, 'w', encoding='utf-8') as file:
    json.dump(
        graph_data,
        file,
        ensure_ascii=False,
        indent=4
    )

print('knowledge graph json 저장 완료')
