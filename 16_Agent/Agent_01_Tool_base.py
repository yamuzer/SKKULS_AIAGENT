import json
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

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


@tool
def find_employee_department(
    employee_name: str
) -> dict:

    '''
    직원 이름으로 해당 직원이 근무하는 부서를 검색한다.
    직원의 소속 부서를 알아야 할 때 사용한다.
    '''

    print('\n')
    print('=' * 70)
    print('find_employee_department 실행')
    print('=' * 70)

    employee = EMPLOYEE_DATA.get(employee_name)

    if employee is None:
        return {
            'found': False,
            'employee_name': employee_name,
            'department': None
        }

    return {
        'found': True,
        'employee_name': employee_name,
        'department': employee['department']
    }



@tool
def find_employee_position(
    employee_name: str
) -> dict:

    '''
    직원 이름으로 해당 직원의 직급을 검색한다.

    사용자가 특정 직원의 직급이나 직책을 질문할 때 사용한다.
    '''


    print('\n')
    print('=' * 70)
    print('find_employee_position 실행')
    print('=' * 70)

    employee = EMPLOYEE_DATA.get(employee_name)

    if employee_name is None:
        return {
            'found': False,
            'employee_name': employee_name,
            'position': None
        }

    return {
        'found': True,
        'employee_name': employee_name,
        'position': employee['position']
    }



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
    find_employee_position,
    calculate_order_total
]

model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0
)

model_wih_tools = model.bind_tools(tools)


'''
def print_registered_tools():
    print('\n')
    print('=' * 70)
    print('registered_tools')
    print('=' * 70)


    for index, tool_object in enumerate(tools, start=1)
'''

def inspect_tool_choice(question: str):

    messages = [
        HumanMessage(content=question)
    ]

    ai_message = model_wih_tools.invoke(messages)

    print('\n[Response Type]')
    print(type(ai_message))

    print('\n[AIMessage.content]')
    print(ai_message.content)

    print('\n[AIMessage.tool_calls]')
    print(ai_message.tool_calls)


    if not ai_message.tool_calls:
        print('\nGemini가 Tool을 선택하지 않았습니다.')
        return ai_message

    print('\n')
    print('Tool Call Detail')

    for index, tool_call in enumerate(ai_message.tool_calls, start=1):
        print(f'\n[Tool call {index}]')
        print(f"name: {tool_call['name']}")
        print(f"args: {tool_call['args']}")
        print(f"id: {tool_call['id']}")


question = '철수는 어느 부서에서 근무하고 있고 직책은 뭐야?'

inspect_tool_choice(question)
