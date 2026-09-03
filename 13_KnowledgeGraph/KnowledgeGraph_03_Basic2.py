import networkx as nx

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

for source, target, data in graph.edges(data=True):
    print(f'{source} -- {data["relation"]} -> {target}')



print('\n1-hop 탐색')
for neighbor in graph.successors('철수'):
    edge_data = graph.get_edge_data('철수', neighbor)
    relation = edge_data['relation']
    if relation == 'WORK_AT':
        print(f'철수가 근무하는 회사: {neighbor}')

# 철수가 일하는 회사의 지역
print('\n2-hop 탐색')
company = None
location = None

for neighbor in graph.successors('철수'):
    edge_data = graph.get_edge_data('철수', neighbor)
    if edge_data['relation'] == 'WORK_AT':
        company = neighbor
        break

if company:
    for neighbor in graph.successors(company):
        edge_data = graph.get_edge_data(company, neighbor)
        if edge_data['relation'] == 'LOCATED_IN':
            location = neighbor
            break
print(f'철수가 근무하는 회사: {company}')
print(f'회사가 위치한 지역: {location}')


# networkx shortest path
# 철수 서울 경로 찾기
print('\n[철수 -> 서울 path]')
path = nx.shortest_path(
    graph,
    source='철수',
    target='서울'
)

print(f'Node path: {path}')


# 관계 포함
print('\n[path + relation]')
for index in range(len(path)-1):
    source = path[index]
    target = path[index+1]
    edge_data = graph.get_edge_data(
        source, target
    )
    print(f'{source} --{edge_data["relation"]} -> {target}')


hop_count = len(path)-1
print('\n[Hop 수]: ')
print(hop_count)