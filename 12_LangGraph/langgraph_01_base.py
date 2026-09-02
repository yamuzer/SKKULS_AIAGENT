from typing import TypedDict
from langgraph.graph import StateGraph, START, END



# state 정의
class GraphState(TypedDict):
    text: str


# node 함수
def add_message(state: GraphState):

    print('add_message node 실행')
    print(state)

    new_text = state['text'] + ' 공부 시작'

    return {
        'text': new_text
    }


builder = StateGraph(GraphState)

builder.add_node(
    'add_message',
    add_message
)

builder.add_edge(
    START,
    "add_message"
)

builder.add_edge(
    'add_message',
    END
)

# 실행 가능한 graph 생성
graph = builder.compile()

init_state = {
    'text': 'LangGraph'
}

result = graph.invoke(init_state)

print('\n최종 결과: ')
print(result)