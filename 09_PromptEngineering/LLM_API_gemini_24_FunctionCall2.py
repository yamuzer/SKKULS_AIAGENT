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

classroom_function_tool = {
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
                'enum' : [
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
            },
            'room_name' : {
                'type' : 'string',
                'description' : (
                    '조회할 강의실 이름'
                ),
                'enum' : [
                    'A실',
                    'B실',
                    'C실',
                    '데이터실',
                    'AI 실',
                    '프로젝트실',
                    '세미나실',
                    '멀티미디어실'
                ]
            }
        },
        'required' : [
            'location',
            'room_name'
        ]
    }
}

def test_function_call(
    question: str
) -> None:
    print_title(f'질문 : {question}')

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=question,
        tools=[
            classroom_function_tool
        ]
    )
    print(f'interaction status : {interaction.status}')

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
            print(interaction.output_text)
        return 

    for index, step in enumerate(function_calls, start=1):
        function_name = getattr(step, 'name', None)
        arguments = getattr(step, 'arguments', None)
        call_id = getattr(step, 'call_id', None) or getattr(step, 'id', None)
        print(f'\n [Function call #{index}]')
        print(f'call_id: {call_id}')
        print(f'function_name: {function_name}')
        print(f'arguments: {arguments}')
    print('\n\n')

test_function_call(
    "서울 교육센터의 A실 정보를 확인해줘"
)

test_function_call(
    "부산 데이터실의 좌석 수와 PC 수량을 확인해줘"
)

test_function_call(
    "대전 AI실에 프로젝터가 있는지 확인해줘"
)