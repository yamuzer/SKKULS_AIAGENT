from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict):

    score: int

    result: str


def check_score(state: GraphState):

    print('\n[check_score 실행]')
    print(f'현재 점수: {state["score"]}')


    return {}


def pass_node(state: GraphState):
    print('\n[pass_node 실행]')
    
    return {
        'result': '합격입니다.'
    }


def fail_node(state: GraphState):
    print('\n[fail_node 실행]')

    return {
        'result': '불합격입니다.'
    }


def route_score(state: GraphState):

    score = state['score']

    if score >= 60:
        return 'pass'

    return 'fail'


builder = StateGraph(GraphState)

builder.add_node(
    'check_score',
    check_score
)

builder.add_node(
    'pass',
    pass_node
)

builder.add_node(
    'fail',
    fail_node
)


builder.add_edge(
    START,
    'check_score'
)

builder.add_conditional_edges(
    'check_score',
    route_score
)

builder.add_edge(
    'pass',
    END
)

builder.add_edge(
    'fail',
    END
)


graph = builder.compile()

initial_state = {
    'score': 55,
    'return': ''
}

result = graph.invoke(initial_state)

print('\n최종 결과')
print(result)