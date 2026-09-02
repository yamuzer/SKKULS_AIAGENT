from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict):
    text: str
    length: int
    result: str

def calc_length(state: GraphState):
    print('\n [calc_length 실행]')
    print(f'현재 State: {state}')

    text = state['text']

    length = len(text)
    return {
        'length': length
    }

def make_result(state: GraphState):
    print('\n [make_result] 실행')
    print(f'현재 State: {state}')

    text = state['text']
    length = state['length']

    result = f"{text}의 길이는 {length}입니다."
    return {
        'result': result
    }

#  그래프 빌더 생성
builder = StateGraph(GraphState)

# 노드 정의
builder.add_node('calc_length', calc_length)
builder.add_node('make_result', make_result)

# edge 연결
builder.add_edge(
    START,
    'calc_length'
)

builder.add_edge(
    'calc_length',
    'make_result'
)

builder.add_edge(
    'make_result',
    END
)

# 그래프 컴파일
graph = builder.compile()

# 초기값 지정
initial_state = {
    'text': 'langGraph',
    'length': 0,
    'result': ''
}

# 생성된 그래프에 스테이트값 전달
result = graph.invoke(initial_state)


print('\n 최종 출력')
print(result)

