import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.7-flash"

def print_title(title:str):
    print('\n' + '-' * 80)
    print(title)
    print('-' * 80)
    print()

'''
사용자 질문 -> function declaration(document) 추가
-> gemini -> 사용자 질문 확인 후 필요 시 function declaration 확인
-> 필요한 함수 선택 -> arguments 생성 -> 호출
'''

user_question = """
서울 강의장의 A실 좌석 수와 
프로젝트 설치 여부를 확인해줘.
"""

LOCATION_ENUM = [
    '서울',
    '부산',
    '대전',
    '대구',
    '광주',
    '인천',
    '수원',
    '성남',
    '울산',
    '제주'
]

ROOM_ENUM = [
    'A실',
    'B실',
    'C실',
    '데이터실',
    'AI 실',
    '프로젝트실',
    '세미나실',
    '멀티미디어실'
]

get_classroom_info_tool = {
    'type' : 'function',
    'name' : 'get_classroom_info',
    'description' : (
        '교육장 지역과 강의 이름을 입력받아 해당 강의실의 좌석 수'
        '프로젝트 설치 여부, pc 수량, 전자칠판, wi-fi, 접근성 정보를 조회할 때 사용하는 함수입니다.'
    ),
    'parameters' : {
        'type' : 'object',
        'properties' : {
            'location' : {
                'type' : 'string',
                'description' : (
                    '교육장이 위치한 지역명.'
                    '예: 서울, 부산, 대전'
                ),
                'enum' : LOCATION_ENUM
            },
            'room_name' : {
                'type' : 'string',
                'description' : (
                    '조회할 강의실 이름'
                ),
                'enum' : ROOM_ENUM
            }
        },
        'required' : [
            'location',
            'room_name'
        ]
    }
}

'''
특정 지역에 있는 모든 강의실 목록 조회
예: 서울 교육센터에는 어떤 강의실이 있나?
'''
get_classroom_by_location_tool = {
    'type': 'function',
    'name': 'get_classrooms_by_location',
    'description': (
        '특정 교육장 지역에 존재하는 모든 강의실 목록을 조회합니다.'
        '사용자 특정 강의실 하나가 아니라 해당 지역의 전체 강의실 목록을'
        '확인하려 할 때 사용합니다.'
    ),
    'parameters':{
        'type': 'object',
        'properties': {
            'location':{
                'type': 'string',
                'description': '교육장 지역',
                'enum' : LOCATION_ENUM
            }
        },
        'required':[
            'location'
        ]
    }
}


'''
PC 수량 조건에 맞는 강의실 검색
예 : PC 30대 이상 강의실을 찾아줘
'''

get_available_pc_room_tool = {
    'type': 'function',
    'name': 'get_available_pc_rooms',
    'description': (
        '전체 교육장 강의실 중에서 사용자가 지정한 최소 PC수량 이상을'
        '보유한 강의실을 검색합니다. PC수량 조건으로 강의실을 찾을 때 사용합니다.'
    ),
    'parameters':{
        'type': 'object',
        'properties': {
            'minimum_pc_count': {
                'type': 'integer',
                'description': '강의실에 필요한 최소 PC수량',
                'minimum': 0
            }
        },
        'required':{
            'minimum_pc_count'
        }
    }
}


TOOLS = [
    get_classroom_info_tool,
    get_classroom_by_location_tool,
    get_available_pc_room_tool
]

def analyze_function_selection(
    question: str, 
    expected_function: str | None,
) -> None:
    print_title(f'사용자 질문: {question}')

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=question,
        tools=TOOLS,
        generation_config={
            'tool_choice': "auto" # auto,any는 무조건 선택하도록, none 사용안함 ...
        }
    )

    print(f'\ninteraction status : {interaction.status}')

    steps = interaction.steps or []

    for index, step in enumerate(steps, start=1):
        print(f'[{index}] {getattr(step, 'type', None)}')

    function_calls = [
        step
        for step in steps
        if getattr(step, 'type', None) == 'function_call'
    ]

    if not function_calls:
        if interaction.output_text:
            print(f'\ngemini가 자연어로 답변함')
        
        if expected_function is None:
            print('\n예상 결과와 일치 : function이 필요없는 질문')
        else :
            print(f'\n확인 필요: 예상 function: {expected_function}')
            
        return

    selected_names = []
    for index, call in enumerate(function_calls, start=1):
        function_name = getattr(call, 'name', None)
        arguments = getattr(call, 'argumnets', None)
        call_id = getattr(call, 'id', None)

        selected_names.append(function_name)
        
        print(f'id: {call_id}')
        print(f'name: {function_name}')
        print(f'arguments: {arguments}')
        

    print_title('선택 검증')
    print(f'예상 function: {expected_function}')
    print(f'실제 선택 function: {selected_names}')

'''
analyze_function_selection(
    question='서울 A실의 좌석 수와 프로젝트 여부를 확인해줘.',
    expected_function = 'get_classroom_info'
)

analyze_function_selection(
    question='부산 교육센터에는 어떤 강의실이 있는지 전체 목록을 확인해줘',
    expected_function = 'get_classroom_by_location'
)

analyze_function_selection(
    question='pc가 30대 이상 설치된 강의실을 찾아줘',
    expected_function = 'get_available_pc_rooms'
)
'''
analyze_function_selection(
    question='Python의 list와 tuple의 차이를 설명해줘',
    expected_function = '?'
)
analyze_function_selection(
    question='서울 교육 센터의 강의실 목록을 전부 보여줘',
    expected_function = 'get_classroom_by_location'
)