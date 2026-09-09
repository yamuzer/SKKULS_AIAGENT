import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.messages import HumanMessage, ToolMessage
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

# ToolNode => AIMessage.tool_calls를 보고 실제 @tool을 실행한다.

tool_node = ToolNode(tools)

tool_graph_builder = StateGraph(MessagesState)

tool_graph_builder.add_node(
    'tools',
    tool_node
)

tool_graph_builder.add_edge(
    START,
    'tools'
)

tool_graph_builder.add_edge(
    'tools',
    END
)


tool_graph = tool_graph_builder.compile()


def run_tool_node(
        question: str
):
    print('='*70)
    print('agent tool use')
    print('='*70)

    print(f'\n[사용자 질문]:\n{question}')

    human_message = HumanMessage(
        content=question
    )

    ai_message = model_wih_tools.invoke(
        [human_message]
    )

    if not ai_message.tool_calls:
        print('\nNo Tool Call')
        print('gemini가 tool이 필요하지 않다고 판단했습니다.')
        print('[gemini answer]')
        print(ai_message.content)

        return {
            'human_message': human_message,
            'ai_message': ai_message,
            'tool_message': [],
            'graph_result': None
        }


    graph_result = tool_graph.invoke(
        {
            'messages': [
                ai_message
            ]
        }
    )


    '''
    print('\n[전체 graph result]')
    print(graph_result)
    print()
    '''

    all_messages = graph_result.get('messages', [])


    for index, message in enumerate(all_messages, start=1):
        print(index, type(message))

    print()

    tool_messages = [
        message
        for message in all_messages
        if isinstance(message, ToolMessage)
    ]

    print(tool_messages)



if __name__ == "__main__":
    run_tool_node(
        '철수는 어느 부서에서 근무하고 그의 직책은 무엇인가요?'
    )