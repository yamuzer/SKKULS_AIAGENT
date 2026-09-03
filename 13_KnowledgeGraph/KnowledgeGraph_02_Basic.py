import networkx as nx

graph = nx.DiGraph()

# 철수 ->  ABC 

graph.add_node(
    '철수',
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

print('\n[Node 목록]:')

for node in graph.nodes:
    print(node)

print()

print('\n[Node + Property]:')

for node, data in graph.nodes(data=True):
    print(node, data)

print()

print('\n[Edge 목록]:')

for source, target in graph.edges:
    print(f'{source} -> {target}')

print()

print('\n[Edge + Relation]:')

for source, target, data in graph.edges(data=True):
    print(f'{source} --{data}-> {target}')

# 특정 노드가 연결하고 있는 대상 찾기
target_node = "철수"
print(f'\n[{target_node}가 연결된 Node]')

neighbors = graph.successors(target_node) # 기준점에서 나가는 방향
for neighbor in neighbors:
    print(f'{target_node} -> {neighbor}')


print(f'\n[{target_node}의 관계]')
for neighbor in graph.successors(target_node):
    edge_data = graph.get_edge_data(
        target_node,
        neighbor
    )

    relation = edge_data['relation']

    print(f'{target_node} -- {relation} -> {neighbor}')