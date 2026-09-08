import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.messages import HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
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

if not GEMINI_API_KEY:
    raise RuntimeError(
        'GEMINI_API_KEY가 없습니다.'
    )



MAX_TOOL_ROUNDS = 5


EMPLOYEE_DATA = {
    '철수': {
        'department': '데이터분석팀',
        'position': '대리'
    },
    '영희': {
        'department': 'AI개발팀',
        'position': '과장'
    },
    '민수': {
        'department': '서비스기획팀',
        'position': '사원'
    },
    '지수': {
        'department': '클라우드플랫폼팀',
        'position': '대리'
    },
}


DEPARTMENT_DATA = {
    '데이터분석팀':{
        'manager': '김현우',
        'floor': 7
    },
    'AI개발팀':{
        'manager': '박서연',
        'floor': 8
    },
    '서비스기획팀':{
        'manager': '이준호',
        'floor': 5
    },
    '클라우드플랫폼팀':{
        'manager': '최유진',
        'floor': 9
    },

}



@tool
def find_employee_department(
    employee_name: str
) -> dict:

    '''
    직원 이름으로 해당 직원의 소속 부서를 검색한다.

    직원이 어느 부서에서 근무하는지 알아야 할 때 사용한다.

    이 Tool은 부서 이름까지만 반환하며 부서 팀장 정보는 반환하지 않는다.
    '''

    print('\n')
    print('=' * 70)
    print('find_employee_department 실행')
    print('=' * 70)

    employee = EMPLOYEE_DATA.get(employee_name)

    if employee is None:
        result = {
            'found': False,
            'employee_name': employee_name,
            'department': None
        }
    else:
        result = {
            'found': True,
            'employee_name': employee_name,
            'department': employee['department']
        }


    print(f'result: {result}')

    return result


@tool
def find_department_manager(
    department_name: str
) -> dict:
    '''
    부서 이름으로 해당 부서의 팀장을 검색한다.

    부서 이름을 이미 알고 있고
    해당 부서의 팀장이 누구인지 알아야 할 때 사용한다.

    직원 이름을 직접 입력하지 말고
    정확한 부서 이름을 입력해야 한다.
    '''

    print('\n')
    print('=' * 70)
    print('find_department_manager 실행')
    print('=' * 70)

    print(f'department_name: {department_name}')

    department = DEPARTMENT_DATA.get(department_name)


    if department is None:
        result = {
            'found': False,
            'department_name': department_name,
            'manager': None
        }
    else:
        result = {
            'found': True,
            'department_name': department_name,
            'manager': department['manager']
        }

    print(f'result: {result}')

    return result


@tool
def find_department_floor(
    department_name: str
) -> dict:
    '''
    부서 이름으로 해당 부서가 위치한 사무실 층을 검색한다.

    특정 부서가 몇 층에 있는지 알아야 할 때 사용한다.
    '''

    print('\n')
    print('=' * 70)
    print('find_department_floor 실행')
    print('=' * 70)

    print(f'department_name: {department_name}')

    department = DEPARTMENT_DATA.get(department_name)


    if department is None:
        result = {
            'found': False,
            'department_name': department_name,
            'floor': None
        }
    else:
        result = {
            'found': True,
            'department_name': department_name,
            'floor': department['floor']
        }

    print(f'result: {result}')

    return result

    

@tool
def calculate_order_total(
    unit_price: int,
    quantity: int
) -> dict:

    '''
    상품 한개의 가격과 구매 수량을 이용하여
    총 주문 금액을 계산한다.
    '''

    print('\n')
    print('=' * 70)
    print('calculate_order_total 실행')
    print('=' * 70)

    total_price = unit_price * quantity

    return {
        'unit_price': unit_price,
        'quantity': quantity,
        'total_price': total_price
    }



tools = [
    find_employee_department,
    find_department_manager,
    find_department_floor,
    calculate_order_total
]

model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0
)

model_wih_tools = model.bind_tools(tools)

SYSTEM_PROMPT = """
당신은 회산 내부 정보를 조회하는 Tool-Using Agent입니다.

다음 규칙을 반드시 지키세요.
1. 사용자의 질문에 답하기 위해 필요한 정보가 Tool에 있다면 Tool을 사용하세요.
2. Tool의 입력값을 모르는 경우 임의로 추측하지 마세요.
3. 필요한 입력값을 다른 Tool을 통해 얻을 수 있다면 먼저 그 Tool을 사용하세요.
4. Tool 실행 결과를 확인한 뒤 아직 필요한 정보가 있다면 다음 Tool을 호출하세요.
5. 필요한 정보를 모두 얻었다면 Tool을 더 호출하지 말고 사용자에게 자연스러운 한국어로 최종 답변하세요.
6. Tool 결과에 없는 회사 내부 정보를 만들어내지 마세요.


예:

사용자:
"철수가 속한 부서의 팀장은 누구야?"

올바른 과정:

철수의 부서가 필요함
-> find_employee_department

결과:
데이터분석팀

팀장이 필요함
-> find_department_manager
     department_name="데이터분석팀"

결과:
김현우


-> 최종 답변
"""


class AgentState(MessagesState):

    tool_rounds: int


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
                    content='도구 호출 횟수가 너무 많아 요청 처리를 중단했습니다.'
                )
            ]
        }

    model_messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        ),
        *messages
    ]

    response = model_wih_tools.invoke(model_messages)

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

tool_node = ToolNode(tools)


def route_after_agent(
        state: AgentState
) -> Literal[
    'tools',
    'end'
]:

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
        question: str
):

    print('\n')
    print('#'*80)
    print('sequential tool agent')
    print('#'*80)

    print('\n[사용자 질문]')
    print(question)

    initial_state = {
        'messages': [
            HumanMessage(
                content=question
            )
        ],
        'tool_rounds': 0
    }

    result = agent_graph.invoke(
        initial_state
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


    final_answer = result["messages"][-1]

    final_text = getattr(
        final_answer,
        'text',
        None
    )

    print('\n')
    print('='*80)
    print('Final Answer')
    print('='*80)

    if isinstance(final_text, str) and final_text:
        print(final_text)
    else:
        print(final_answer.content)

    return result


run_agent('영희가 속한 부서의 팀장은 누구야?')