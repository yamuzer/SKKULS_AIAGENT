import os
import chromadb
import networkx as nx
import json

from dataclasses import dataclass
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore



from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from langchain.tools import tool, ToolRuntime
from langchain_core.documents import Document
from langchain.messages import HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ENV_PATH = BASE_DIR / "../.env"
load_dotenv(dotenv_path=ENV_PATH)


GEMINI_API_KEY = os.getenv(
    'GEMINI_API_KEY'
)

GEMINI_MODEL = os.getenv(
    'GEMINI_MODEL',
    'gemini-3.7-flash'
)

GEMINI_EMBEDDING_MODEL = os.getenv(
    'GEMINI_EMBEDDING_MODEL',
    'gemini-embedding-2'
)

if not GEMINI_API_KEY:
    raise RuntimeError(
        'GEMINI_API_KEY가 없습니다.'
    )



@dataclass(frozen=True)
class UserContext:
    user_id: str


class AgentState(MessagesState):

    tool_rounds: int


'''
short term memory

InMemorySaver

thread_id별로 대화를 유지한다.
'''

checkpointer = InMemorySaver()



'''
long term memory

thread id와 독립적

user id를 Namespace에 사용
'''

store = InMemoryStore()


'''
long term memory Namespace 

user-001:

(
    'user-001',
    'memories'
)
'''

def create_memory_namespace(
        user_id: str
):
    return (
        user_id,
        'memories'
    )


@tool
def save_user_memory(
    memory_key: str,
    memory_value: str,
    runtime: ToolRuntime[UserContext]
) -> dict:

    '''
    현재 사용자의 정보를 Long-Term Memory에 저장한다.

    사용자가 다른 대화에서도 기억해 달라고 명시적으로 요청했을 때 사용한다.

    memory_key에는 기억의 종류를 나타내고 짥고 안정적인 영어 snake_case 이름을 사용한다.

    예:
    preferred_vector_db
    favorite_framework
    learning_goal

    memory_value에는 실제 기억할 값을 지정한다.

    user_id는 Tool Argument로 입력하지 않는다.
    ToolRuntime Context에서 자동으로 가져온다.
    '''

    print('\n')
    print('='*80)
    print('[Tool Execution: save_user_memory]')
    print('='*80)

    user_id = runtime.context.user_id
    print(f'user_id: {user_id}')
    print(f'memory_key: {memory_key}')
    print(f'memory_value: {memory_value}')

    memory_store = runtime.store

    if memory_store is None:
        return {
            'saved': False,
            'reason': 'Long Term Store가 연결되어 있지 않습니다.'
        }

    namespace = create_memory_namespace(user_id)


    memory_store.put(
        namespace,
        memory_key,
        {
            'memory_key': memory_key,
            'memory_value': memory_value
        }
    )

    result = {
        'saved': True,
        'user_id': user_id,
        'memory_key': memory_key,
        'memory_value': memory_value
    }

    print('\n[Save Result]')
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    return result


'''
long term memory 전체 조회
'''
@tool
def list_user_memories(
    runtime: ToolRuntime[UserContext]
) -> dict:

    '''
    현재 사용자의 Long-Term Memory 목록을 조회한다.

    사용자가 이전 대화에서 저장한 정보, 선호도, 학습 목표 등을 기억하는지 물어볼 때 사용한다.

    user_id는 Tool Argument로 입력하지 않는다.
    ToolRuntime Context에서 자동으로 가져온다.
    '''

    print('\n')
    print('='*80)
    print('[Tool Execution: list_user_memories]')
    print('='*80)

    user_id = runtime.context.user_id
    print(f'user_id: {user_id}')

    memory_store = runtime.store

    if memory_store is None:
        return {
            'found': False,
            'user_id': user_id,
            'count': 0,
            'memories': [],
            'reason': 'Long-Term Store가 연결되어 있지 않습니다.'
        }

    namespace = create_memory_namespace(user_id)

    items = memory_store.search(
        namespace,
        limit=100
    )

    memories = []

    for item in items:
        memories.append(
            {
                'key': item.key,
                'value': item.value.get('memory_value')
            }
        )

    result = {
        'found': len(memories) > 0,
        'user_id': user_id,
        'count': len(memories),
        'memories': memories
    }

    print('\n[Memory Result]')
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    return result

    
@tool
def delete_user_memory(
    memory_key: str,
    runtime: ToolRuntime[UserContext]
) -> dict:
    '''
    현재 사용자의 특정 Long-Term Memory를 삭제한다.

    사용자가 이전에 저장한 장기 기억을 더 이상 기억하지 말라고 요청할 때 사용한다.

    memory_key에는 삭제할 기억의 key를 입력한다.
    '''

    print('\n')
    print('='*80)
    print('[Tool Execution: list_user_memories]')
    print('='*80)

    user_id = runtime.context.user_id
    print(f'user_id: {user_id}')

    memory_store = runtime.store

    if memory_store is None:
        return {
            'deleted': False,
            'reason': 'Store가 없습니다.'
        }

    namespace = create_memory_namespace(user_id)

    existing = memory_store.get(
        namespace,
        memory_key
    )

    if existing is None:

        return {
            'deleted': False,
            'user_id': user_id,
            'memory_key': memory_key,
            'reason': '해당 Memory가 없습니다.'
        }

    memory_store.delete(
        namespace,
        memory_key
    )

    return {
        'deleted': True,
        'user_id': user_id,
        'memory_key': memory_key
    }



tools = [
    save_user_memory,
    list_user_memories,
    delete_user_memory
]


def print_tool_schemas():

    print('\n')
    print('='*80)
    print('[Tool Schemas]')
    print('='*80)

    for tool_object in tools:
        print('\n')
        print('='*80)
        print(tool_object.name)
        print('='*80)

        schema_object = tool_object.tool_call_schema


        if isinstance(schema_object, dict):
            schema = schema_object

        else:
            schema_object.model_json_schema()

        print('\n[LLM Visible Schema]')
        print(
            json.dumps(
                schema,
                ensure_ascii=False,
                indent=2
            )
        )

        properties = schema.get(
            'properties',
            {}
        )

        print('\n[LLM이 생성해야 하는 Argument]')

        if properties:
            for argument_name in properties.keys():
                print(f'- {argument_name}')

        else:
            print('- 없음')

        print(
            f'\nruntime 노출 여부: {"runtime" in properties}'
        )


model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0,
    max_retries=2
)

model_with_tools = model.bind_tools(tools)

SYSTEM_PROMPT = """
당신은 Short-Term Memory와 Long-Term Memory를 구분해서 사용하는 Memory Agent입니다.



[Short-Term Memory]

현재 thread의 message history는 LangGraph Checkpointer가 관리합니다.

현재 대화에서 앞서 사용자가 말한 내용은 messages를 보고 답할 수 있습니다.

이 정보는 다른 thread에는 자동으로 공유되지 않습니다.


예:

사용자: "이 대화 안에서만 기억해 내가 지금 복습하는 주제는 ToolRuntime이야. "

같은 thread에서:

"내가 복습한다고 한 주제가 뭐였지?"

-> 이전 Message를 보고 ToolRuntime이라고 답합니다.



[Long-Term Memory]

사용자가 다음과 같이 명확하게 요청하면 Long-Term Memory Tool을 사용합니다.

"다른 대화에서도 기억해줘."
"장기 기억에 저장해줘."
"다음 대화에서도 기억해줘."
"앞으로 기억해줘."

이 경우:

save_user_memory를 사용하세요.



[save_user_memory]

Long-Term Memory를 저장합니다.

memory_key는 짧고 안정적인 영어 snake_case를 사용하세요.

예:

preferred_vector_db
preferred_framework
learning_goal
favoriate_language

memory_value에는 실제 기억할 정보를 넣습니다.

user_id는 Argument로 만들지 마세요.
ToolRuntime Context에서 자동으로 얻습니다.



[list_user_memories]

사용자가 이전 대화에서 저장한 Long-Term Memory를 물어보는 경우 사용하세요.

예:

"내가 선호하는 Vector DB가 뭐였지? 장기 기억에서 찾아줘."

"다른 대화에서 내가 기억해달라고 한 내용 알려줘."

이 Tool은 현재 사용자의 Memory만 조회합니다.



[delete_user_memory]

사용자가 저장된 장기 기억을 삭제하라고 명확하게 요청할 때 사용하세요.



[중요 규칙]

1. 현재 thread 안의 대화 내용만 필요한 경우 Long-Term Memory Tool을 사용하지 마세요.
2. 사용자가 명확하게 Long-Term 저장을 요청하지 않았다면 임의로 장기 기억에 저장하지 마세요.
3. Long-Term Memory를 묻는 질문에는 list_user_memories를 사용하세요.
4. 다른 사용자의 Memory를 추측하거나 조회하지 마세요.
5. user_id를 Tool Argument로 만들지 마세요.
6. Tool 결과에 없는 Memory를 만들지 마세요.
7. 같은 Tool을 불필요하게 반복 요청하지 마세요.
8. 일반 지식 질문에는 Memory Tool을 사용하지 않아도 됩니다.
"""

MAX_TOOL_ROUNDS = 5


def agent_node(
    state: AgentState
):

    print('='*70)
    print('[Agent Node 실행]')
    print('='*70)

    messages = state['messages']

    tool_rounds = state.get('tool_rounds', 0)

    print(f'message 수: {len(messages)}')
    print(f'tool round: {tool_rounds}')

    if tool_rounds >= MAX_TOOL_ROUNDS:
        print('\n최대 Tool Round에 도달했습니다.')

        return {
            'messages':[
                AIMessage(
                    content='도구 호출 횟수 제한에 도달하여 요청을 완료하지 못했습니다.'
                )
            ]
        }

    model_messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        ),
        *messages
    ]

    response = model_with_tools.invoke(model_messages)

    print('\n[Agent response]')
    print(response.content)

    print('\n[Tool Calls]')
    print(response.tool_calls)    

    if response.tool_calls:
        new_tool_rounds = tool_rounds + 1
        print(f'\nTool Round: {tool_rounds} -> {new_tool_rounds}')

        return {
            'messages':[
                response
            ],
            'tool_rounds': new_tool_rounds
        }

    print('\n추가 Tool Call 없음')
    print('-> 최종 답변')

    return {
        'messages': [
            response
        ]
    }



tool_node = ToolNode(
    tools,
    handle_tool_errors=True
)



def route_after_agent(
        state: AgentState
):

    print('='*70)
    print('[Router 실행]')
    print('='*70)


    last_message = state['messages'][-1]

    tool_calls = getattr(
        last_message,
        'tool_calls',
        []
    )

    if tool_calls:
        print(f'Tool call: {len(tool_calls)}')
        print('-> ToolNode')
        print('Tool call 있음')

        return 'tools'

    print(f'Tool call 없음')
    print('-> END')

    return 'end'


builder = StateGraph(
    AgentState,
    context_schema=UserContext
)

builder.add_node(
    'agent',
    agent_node
)

builder.add_node(
    'tools',
    tool_node
)

builder.add_edge(
    START,
    'agent'
)


builder.add_conditional_edges(
    'agent',
    route_after_agent,
    {
        'tools': 'tools',
        'end': END
    }
)

builder.add_edge(
    'tools',
    'agent'
)

agent_graph = builder.compile(
    checkpointer=checkpointer,
    store=store
)



def extract_tool_sequence(
        messages
):

    sequence = []

    for message in messages:
        if not isinstance(message, AIMessage):
            continue

        for tool_call in message.tool_calls:
            sequence.append(
                tool_call.get('name')
            )

    return sequence



def get_ai_text(
        message
):
    text = getattr(
        message,
        'text',
        None
    )

    if isinstance(text, str) and text:
        return text

    return message.content


def print_message(
        index,
        message
):

    print()
    print('='*70)
    print(f'Message {index}')
    print('='*70)

    if isinstance(message, HumanMessage):
        print('type: HumanMessage')
        print(message.content)

    elif isinstance(message, ToolMessage):
        print('type: ToolMessage')
        print(f'Tool: {message.name}')
        print(f'Tool Call ID: {message.tool_call_id}')
        print(message.content)

    elif isinstance(message, AIMessage):
        print('type: AIMessage')

        if message.tool_calls:
            print('\n[Tool Calls]')

            for tool_call in message.tool_calls:
                print(f'\nname: {tool_call.get("name")}')
                print(f'args: {tool_call.get("args")}')
                print(f'id: {tool_call.get("id")}')
    else:
        text = getattr(
            message,
            'text',
            None
        )

        if isinstance(text, str) and text:
            print()
            print(text)

        else:
            print(message.content)




def run_turn(
        question: str,
        user_id: str,
        thread_id: str
):

    print('\n')
    print('#'*80)
    print('Memory agent turn')
    print('#'*80)

    print(f'\nuser_id: {user_id}')
    print(f'thread_id: {thread_id}')

    print('\n[사용자 질문]')
    print(question)


    config = {
        'configurable':{
            'thread_id': thread_id
        }
    }
    
    result = agent_graph.invoke(
        {
            'messages':[
                HumanMessage(
                    content=question
                )
            ],
            'tool_rounds': 0
        },
        config=config,
        context=UserContext(
            user_id=user_id
        )
    )

    


    print('\n')
    print('#'*80)
    print('[Thread Message Count]')
    print('#'*80)

    print(f'총 Message 수: {len(result["messages"])}')
    print(f'총 Tool Round: {result.get("tool_rounds", 0)}')

    for index, message in enumerate(result['messages'], start=1):
        print_message(
            index,
            message
        )


    actual_sequence = extract_tool_sequence(
        result['messages']
    )

    print('\n')
    print('='*80)
    print('Tool Sequence')
    print('='*80)

    if actual_sequence: 
        print(f' -> '.join(actual_sequence))

    else:
        print('Tool 사용 안 함')


    final_answer = result["messages"][-1]

    print('\n')
    print('='*80)
    print('Final Answer')
    print('='*80)

    print(get_ai_text(final_answer))

    return result


def run_short_term_demo():
    print('\n\n')
    print('='*80)
    print('Short_Term Memory Demo')
    print('='*80)

    user_id = 'user-001'
    thread_a = 'thread-short-A'
    thread_b = 'thread-short-B'

    run_turn(
        question=(
            '이 대화 안에서만 기억해. '
            '지금 내가 복습하고 있는 주제는 ToolRuntime이야.'
        ),
        user_id=user_id,
        thread_id=thread_a
    )

    run_turn(
        question='내가 이 대화에서 복습한다고 말한 주제가 뭐였지?',
        user_id=user_id,
        thread_id=thread_a
    )

    run_turn(
        question='내가 이 대화에서 복습한다고 말한 주제가 뭐였지? 장기 기억에는 저장하지 않았어.',
        user_id=user_id,
        thread_id=thread_b
    )




def run_long_term_demo():
    print('\n\n')
    print('='*80)
    print('Long_Term Memory Demo')
    print('='*80)

    user_1 = 'user-001'
    user_2 = 'user-002'

    run_turn(
        question=(
            '다른 대화에서도 기억할 수 있도록 장기 기억에 저장해줘. '
            '내가 선호하는 VectorDB는 ChromaDB야. '
        ),
        user_id=user_1,
        thread_id='thread-long-A'
    )

    '''
    run_turn(
        question=(
            '새로운 대화인데 장기 기억에서 내가 선호한다고 저장한 ' 
            'VectorDB가 무엇인지 찾아줘.'
        ),
        user_id=user_1,
        thread_id='thread-long-B'
    )
    '''


    run_turn(
        question=(
            '새로운 대화인데 장기 기억에서 내가 선호한다고 저장한 ' 
            'VectorDB가 무엇인지 찾아줘.'
        ),
        user_id=user_2,
        thread_id='thread-long-C'
    )


def run_multiple_memory_demo():

    print('\n\n')
    print('='*80)
    print('Multiple Long_Term Memory Demo')
    print('='*80)

    user_id = 'user-003'

    run_turn(
        question=(
            '앞으로 기억해줘. 내가 선호하는 '
            'Agent Framework는 LangGraph야. '
        ),

        user_id=user_id,
        thread_id='thread-multi-1'
    )

    run_turn(
        question=(
            '다른 대화에서도 기억해줘. '
            '내가 현재 집중해서 공부하는 주제는 Agentic RAG야.'
        ),

        user_id=user_id,
        thread_id='thread-multi-2'
    )

    run_turn(
        question=(
            '장기 기억에 저장된 내 선호 Framework와 ' \
            '현재 학습 주제를 알려줘.'
        ),

        user_id=user_id,
        thread_id='thread-multi-3'
    )



def run_delete_memory_demo():
    print('\n\n')
    print('='*80)
    print('Multiple Long_Term Memory Demo')
    print('='*80)

    user_id = 'user-delete' 

    run_turn(
        question='장기 기억에 저장해줘. 내가 선호하는 Vector DB는 ChromaDB야.',
        user_id=user_id,
        thread_id='thread-delete-1'
    )

    run_turn(
        question='이전에 장기 기억에 저장한 선호 Vector DB 정보를 삭제해줘.',
        user_id=user_id,
        thread_id='thread-delete-2'
    )

    run_turn(
        question='이전에 장기 기억에 저장한 선호 Vector DB 정보를 삭제해줘.',
        user_id=user_id,
        thread_id='thread-delete-2'
    )

    run_turn(
        question=(
            '새로운 대화인데 장기 기억에서 내가 선호한다고 저장한 ' 
            'VectorDB가 무엇인지 찾아줘.'
        ),
        user_id=user_id,
        thread_id='thread-delete-3'
    )



DEMO_MODE = 'delete'

if DEMO_MODE == 'short':
    run_short_term_demo()

elif DEMO_MODE == 'long':
    run_long_term_demo()

elif DEMO_MODE == 'multiple':
    run_multiple_memory_demo()

elif DEMO_MODE == 'delete':
    run_delete_memory_demo()