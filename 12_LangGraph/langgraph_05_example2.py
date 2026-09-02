from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict):
    value: int # 현재값
    target: int # 목표값
    retry_count: int # 현재 시도 횟수
    max_retries: int # 최대 시도 횟수
    status: str # 현재 처리 상태
    result: str # 최종 결과


def process_node(state: GraphState):
    print('\n[process_node 실행]')
    current_value = state['value']
    retry_count = state['retry_count']
    print(f'현재 value: {current_value}')
    print(f'현재 시도 횟수: {retry_count}')

    new_value = current_value + 3
    new_retry_count = retry_count + 1

    print(f'처리 후 value: {new_value}')
    print(f'처리 후 시도 횟수: {new_retry_count}')

    return {
        'value' : new_value,
        'retry_count': new_retry_count,
        'status': 'processed'
    }

def check_result(state:GraphState):
    print('\n [check_result] 실행')

    value = state['value']
    target = state['target']
    retry_count = state['retry_count']
    max_retries = state['max_retries']

    print(f'현재 값: {value}')
    print(f'목표 값: {target}')
    print(f'시도 횟수: {retry_count}')

    return {
        'status': 'checking'
    }

def route_result(state:GraphState):
    value = state['value']
    target = state['target']
    retry_count = state['retry_count']
    max_retries = state['max_retries']

    print('\n [route_result 실행]')
    
    if value >= target:
        print('판정: 성공')
        return 'success'

    if retry_count >= max_retries:
        print('판정: 실패')
        return 'fail'

    print('판정: 재시도')
    return 'retry'


def retry_node(state: GraphState):
    print('\n[retry_node 실행]')
    print(f"{state['retry_count']}번째 처리 결과가 목표에 도달하지 못했습니다.")

    print('다시 처리합니다.')

    return {
        'status': 'retrying'
    }

def success_node(state: GraphState):
    print('\n[success_node 실행]')

    result = (
        f"성공: Value가 {state['value']}이 되어 "
        f"목표 {state['target']}에 도달했습니다."
    )
    return {
        'status': 'success',
        'result': result
    }


    
def failed_node(state: GraphState):
    print('\n[fail_node 실행]')
    
    result = (
        f"실패: 최대 {state['max_retries']}번 시도했지만"
        f"목표 {state['target']}에 도달하지 못했습니다."
    )
    print('다시 처리합니다.')

    return {
        'status': 'fail',
        'result': result
    }


builder = StateGraph(GraphState)

builder.add_node(
    'process',
    process_node
)

builder.add_node(
    'check_result',
    check_result
)

builder.add_node(
    'retry',
    retry_node
)


builder.add_node(
    'success',
    success_node
)

builder.add_node(
    'failed',
    failed_node
)


builder.add_edge(
    START,
    'process'
)


builder.add_edge(
    'process',
    'check_result'
)

builder.add_conditional_edges(
    'check_result',
    route_result,
    {
        'success': 'success',
        'retry': 'retry',
        'failed':'failed'
    }
)

builder.add_edge(
    'retry', 
    'process'
)

builder.add_edge(
    'success',
    END
)

builder.add_edge(
    'failed',
    END
)

graph = builder.compile()

initial_state: GraphState={
    'value': 1,
    'target': 10,
    'retry_count': 0,
    'max_retries': 5,
    'status': 'ready',
    'result': ""
}

result = graph.invoke(initial_state)

print('\n최종 state')
print(result)
print('\n최종 결과: ')
print(result['result'])