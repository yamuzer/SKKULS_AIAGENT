from dataclasses import dataclass
from typing import TypedDict, Literal

from langgraph.runtime import Runtime
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

class GraphState(TypedDict):
    action: Literal[
        'save',
        'read'
    ]
    # 저장할 학습 언어
    learning : str

    result : str

# 사용자 구분
# 같은 사용자가 여러 thread를 만들 수 이기 때문에 user_id와 thread_id를 분리
@dataclass
class Context:
    user_id : str

# long-term memory 처리 node
def memory_node(
    state: GraphState,
    runtime: Runtime[Context]
):
    print('\n[memory_node 실행]')

    user_id = runtime.context.user_id

    print(f'현재 user_id: {user_id}')

    namespace = ( # 디렉토리 /users/user-001/profile/
        'users',
        user_id,
        'profile'
    )

    print(f'namespace: {namespace}')

    action = state['action']

    if action == "save":
        learning = state['learning']
        print(f'\n저장할 학습 언어: {learning}')

        runtime.store.put(
            namespace,
            "learning",
            {
                'language': learning
            }
        )

        return {
            'result': f"{learning} 학습 정보를 Long-term Memory에 저장했습니다."
        }

    memory = runtime.store.get(
        namespace,
        'learning'
    )

    if memory: 
        language = memory.value['language']
        print(f'\n저장된 학습 언어: {language}')

        return {
            'result': f'현재 공부하고 있는 언어는 {language}입니다.'
        }

    return {
        'result': '저장된 학습 정보가 없습니다.'
    }


builder = StateGraph(
    GraphState,
    context_schema=Context
)

builder.add_node(
    'memory',
    memory_node
)

builder.add_edge(
    START,
    'memory'
)

builder.add_edge(
    'memory',
    END
)

# short-term용
checkpointer = InMemorySaver()

# long-term용
store = InMemoryStore()

graph = builder.compile(
    checkpointer=checkpointer,
    store=store
)

user_context = Context(
    user_id="user-001"
)

# 첫번째 thread
config_a = {
    'configurable': {
        'thread_id': 'thread-A'
    }
}
# 두번째 thread
config_b = {
    'configurable': {
        'thread_id': 'thread-B'
    }
}

# Thread A ->Long-term 메모리에 저장
print('\n Thread A - Memory 저장')
result_a = graph.invoke(
    {
        'action': 'save',
        'learning': 'Python',
        'result': '',
    },
    config = config_a,
    context=user_context
)

print('\nThread-A 결과:')
print(result_a['result'])

# Thread B에서 Long-term 메모리 조회
print('\n Thread B - Memory 조회')

result_b = graph.invoke(
    {
        'action': 'read',
        'learning': '',
        'result': ''
    },
    config = config_b,
    context=user_context
)
print('\nThread-B 결과:')
print(result_b['result'])
