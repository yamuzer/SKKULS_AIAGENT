import os
import chromadb
import networkx as nx
import json

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


DEPARTMENT_POLICY = {

    # ========================================================
    # 데이터분석팀
    # ========================================================

    "데이터분석팀": {

        "재택근무": (
            "데이터분석팀은 주 2회까지 "
            "재택근무를 신청할 수 있습니다."
        ),

        "교육비": (
            "데이터분석팀은 연간 최대 "
            "150만원의 직무 교육비를 "
            "지원받을 수 있습니다."
        ),

        "장비": (
            "데이터분석팀은 분석용 고성능 노트북과 "
            "추가 모니터를 신청할 수 있습니다."
        ),
    },


    # ========================================================
    # AI개발팀
    # ========================================================

    "AI개발팀": {

        "재택근무": (
            "AI개발팀은 프로젝트 일정에 따라 "
            "주 3회까지 재택근무가 가능합니다."
        ),

        "교육비": (
            "AI개발팀은 연간 최대 "
            "200만원의 AI 관련 교육비와 "
            "학회 참가비를 지원받을 수 있습니다."
        ),

        "장비": (
            "AI개발팀은 GPU 개발 서버와 "
            "고성능 개발 장비를 사용할 수 있습니다."
        ),
    },


    # ========================================================
    # 서비스기획팀
    # ========================================================

    "서비스기획팀": {

        "재택근무": (
            "서비스기획팀은 주 1회 "
            "재택근무가 가능합니다."
        ),

        "교육비": (
            "서비스기획팀은 연간 최대 "
            "100만원의 직무 교육비를 "
            "지원받을 수 있습니다."
        ),

        "장비": (
            "서비스기획팀은 기본 업무용 노트북과 "
            "회의용 태블릿을 신청할 수 있습니다."
        ),
    },
}


class AgentState(MessagesState):

    user_id: str

    user_name: str

    department: str

    role: str

    tool_rounds: int


@tool
def get_current_user_profile(
    runtime: ToolRuntime
) -> dict:
    '''
    현재 대화를 사용하고 있는 사용자의 이름, 부서, 직급 정보를 조회한다.

    사용자가 자신의 이름, 부서 또는 직급을 질문할 때 사용한다.

    사용자 이름이나 부서를 Tool Argument로 입력하지 않는다.
    '''

    print('\n')
    print('='*80)
    print('[Tool Execution: get_current_user_profile]')
    print('='*80)

    state = runtime.state
    print('\n[State Keys]')
    try:
        print(list(state.keys()))
    except Exception:
        print(type(state))


    user_id = state.get('user_id')
    user_name = state.get('user_name')
    department = state.get('department')
    role = state.get('role')

    result = {
        'user_id': user_id,
        'user_name': user_name,
        'department': department,
        'role': role
    }

    print('\n[Profile Result]')
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    return result



@tool
def search_my_department_policy(
    topic: str,
    runtime: ToolRuntime
) -> dict:
    '''
    현재 사용자가 속한 부서의 내부 정책을 검색한다.

    재택근무, 교육비, 장비 정책 등을 확인할 때 사용한다.

    사용자의 부서는 Tool Argument로 입력하지 않는다.
    현재 LangGraph State에서 자동으로 확인한다.

    topic 예:
    재택근무, 교육비, 장비
    '''

    print('\n')
    print('='*80)
    print('[Tool Execution: search_my_department_policy]')
    print('='*80)

    print(f'\nModel Argument - topic : {topic}')

    state = runtime.state
    user_name = state.get('user_name')
    department = state.get('department')

    print(f'\nRuntime State user_name: {user_name}')
    print(f'\nRuntime State department: {department}')

    department_policy = DEPARTMENT_POLICY.get(department)

    # print()
    # print('!'*100)
    # print(department_policy)
    # print('!'*100)

    if department_policy is None:

        result = {
            'found': False,
            'user_name': user_name,
            'department': department,
            'topic': topic,
            'policy': None,
            'reason': '해당 부서의 정책 데이터가 없습니다.'
        }

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        return result

    policy = department_policy.get(topic)

    if policy is None:
        result = {
            'found': False,
            'user_name': user_name,
            'department': department,
            'topic': topic,
            'policy': None,
            'available_topics': list(department_policy.keys())
        }

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        return result


    result = {
        'found': True,
        'user_name': user_name,
        'department': department,
        'topic': topic,
        'policy': policy
    }

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    return result


@tool
def get_last_user_message(
    runtime: ToolRuntime
) -> dict:
    '''
    현재 LangGraph State에서 가장 최근 사용자의 메시지를 확인한다.

    사용자가 자신이 마지막으로 무엇을 입력했는지 확인하고 싶을 때 사용한다.
    '''

    print('\n')
    print('='*80)
    print('[Tool Execution: get_last_user_message]')
    print('='*80)

    messages = runtime.state.get('messages', [])

    print(f'\n현재 Message 수: {len(messages)}')

    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            result = {
                'found': True,
                'message': message.content
            }

            print('\n[Last User Message]')
            print(result['message'])

            return result

    return {
        'found': False,
        'message': None
    }


@tool
def get_conversation_state_info(
    runtime: ToolRuntime
) -> dict:
    '''
    현재 LangGraph State의 메시지 수와 현재 사용자 정보를 확인한다.

    현재 Agent State 상태를 확인해야 할 때 사용한다.
    '''

    print('\n')
    print('='*80)
    print('[Tool Execution: get_conversation_state_info]')
    print('='*80)

    state = runtime.state

    messages = state.get('messages', [])

    result = {
        'message_count': len(messages),
        'user_id': state.get('user_id'),
        'user_name': state.get('user_name'),
        'department': state.get('department'),
        'role': state.get('role'),
        'tool_rounds': state.get('tool_rounds', 0)
    }

    print()
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    return result


tools = [
    get_current_user_profile,
    search_my_department_policy,
    get_last_user_message,
    get_conversation_state_info
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
당신은 회사 내부 사용자 State를 활용할 수 있는 Tool-Using Agent입니다.

Tool은 LangGraph의 현재 State에 ToolRuntime을 통해 접근 할 수 있습니다.



[get_current_user_profile]
현재 사용자의 이름, 부서 직급을 조회합니다.

현재 사용자의 신원 정보가 필요한 질문에는 이 Tool을 사용하세요.

사용자의 이름, 부서 또는 직급을 Tool Argument로 추측하지 마세요.


[search_my_department_poliy]
현재 사용자가 속한 부서의 정책을 검색합니다.

모델이 생성해야 하는 Argument는 topic뿐입니다.

사용 가능한 topic:
재택근무
교육비
장비

예:

사용자:"내 부서의 재택근무 정책을 알려줘."

올바른 Tool Call:
search_my_department_policy(
    topic="재택근무"
)

department를 Argument로 만들지 마세요.

ToolRuntime이 LangGraph State에서 현재 부서를 직접 읽습니다.



[get_last_user_message]
현재 LangGraph State에 저장된 가장 최근 HumanMessage를 확인합니다.



[get_conversation_state_info]
현재 대화 State의 사용자 정보와 Message 개수 등을 확인합니다.



[중요 규칙]
1. 현재 사용자 이름, 부서, 직급을 추측하지 마세요.
2. 현재 사용자 정보가 필요한 경우 Tool을 사용하세요.
3. 부서 정책 검색에서 department를 Tool Argument로 생성하지 마세요.
4. search_my_department_policy에는 topic만 전달하세요.
5. Tool 결과를 받은 후 자연스러운 한국어로 답하세요.
6. 같은 정보를 얻기 위해 같은 Tool을 불필요하게 반복 호출하지 마세요.
7. Python 문법이나 일반 상식처럼 현재 사용자 State가 필요없는 질문은 
   Tool을 호출하지 않고 직접 답변하세요.
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


builder = StateGraph(AgentState)

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

agent_graph = builder.compile()



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




def run_agent(
        question: str,
        user_id: str,
        user_name: str,
        department: str,
        role: str,
        expected_tool: str
):

    print('\n')
    print('#'*80)
    print('state aware tool agent')
    print('#'*80)

    print('\n[사용자 질문]')
    print(question)

    print(expected_tool)


    initial_state = {
        'messages': [
            HumanMessage(
                content=question
            )
        ],
        'user_id': user_id,
        'user_name': user_name,
        'department': department,
        'role': role,
        'tool_rounds': 0,
    }

    result = agent_graph.invoke(
        initial_state,
        config={
            'recursion_limit': 15
        }
    )


    print('\n')
    print('#'*80)
    print('execution history')
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


TEST_CASES = [
    {
        'question': '내 이름과 소속 부서, 직급을 알려줘',
        'user_id': 'user-001',
        'user_name': '철수',
        'department': '데이터분석팀',
        'role': '대리',
        'expected': 'get_current_user_profile'
    },
    {
        'question': '내 부서의 재택근무 정책을 알려줘.',
        'user_id': 'user-001',
        'user_name': '철수',
        'department': '데이터분석팀',
        'role': '대리',
        'expected': 'search_my_department_policy'
    },
    {
        'question': '우리 부서의 교육비 지원 정책은 어떻게 돼?',
        'user_id': 'user-001',
        'user_name': '철수',
        'department': '데이터분석팀',
        'role': '대리',
        'expected': 'search_my_department_policy'
    },
    {
        'question': '내가 방금 입력한 메시지가 뭐야?',
        'user_id': 'user-001',
        'user_name': '철수',
        'department': '데이터분석팀',
        'role': '대리',
        'expected': 'get_last_user_message'
    },
    {
        'question': '현재 대화 State 정보를 확인해줘.',
        'user_id': 'user-002',
        'user_name': '영희',
        'department': 'AI개발팀',
        'role': '과장',
        'expected': 'get_conversation_state_info'
    },
]

RUN_ALL_EXAMPLES = False

if RUN_ALL_EXAMPLES:
    for index, test in enumerate(TEST_CASES, start=1):
        print('\n\n')
        print('='*80)
        print(f'Example {index}')
        print('='*80)

        run_agent(
            question=test['question'],
            user_id=test['user_id'],
            user_name=test['user_name'],
            department=test['department'],
            role=test['role'],
            expected_tool=test['expected'],
        )

else:
    test = TEST_CASES[3]
    run_agent(
        question=test['question'],
        user_id=test['user_id'],
        user_name=test['user_name'],
        department=test['department'],
        role=test['role'],
        expected_tool=test['expected'],
    )