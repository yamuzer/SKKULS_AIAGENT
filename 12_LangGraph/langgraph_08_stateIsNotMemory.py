from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class GraphState(TypedDict):
    name: str
    count: int

def increase_count(state:GraphState):
    print('\n[increase_count 실행]')

    print(f'Node가 받은 state: \n{state}')
    current_count = state['count']
    new_count = current_count + 1
    return {
        'count': new_count
    }


builder = StateGraph(GraphState)

builder.add_node(
    'increase_count',
    increase_count
)

builder.add_edge(
    START,
    'increase_count'
)

builder.add_edge(
    'increase_count',
    END
)


graph = builder.compile()

initial_state = {
    'name':'철수',
    'count':0
}

result = graph.invoke(initial_state)

print('\n첫번째 실행 결과:')
print(result)

print('\n두번째 graph 실행:')
result2 = graph.invoke(
    {
        'name':"영희",
        'count':0
    }
)
print('\n두번째 실행 결과:')
print(result2)
# state는 메모리가 아니다. 구현해야함