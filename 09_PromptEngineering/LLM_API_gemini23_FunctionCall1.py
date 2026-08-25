import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
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
사용자 질문 -> function declaration(document) 추가 -> gemini
-> 사용자 질문 확인 후 필요 시 function declaration(document) 확인
-> 필요한 함수 선택 -> arguments 생성 -> 호출
'''

user_question = """
서울 강의장의 A실 좌석 수와
프로젝트 설치 여부를 확인해줘.
"""

classroom_function_tool = {
    'type': 'function',
    'name': 'get_classroom_info',
    'description':(
        '교육장 지역과 강의 이름을 입력받아 해당 강의실의 좌석 수, 프로젝트 설치 여부, '
        'PC 수량 등의 정보를 조회합니다.'
    ),
    'parameters':{
        'type': 'object',
        'properties':{
            'location':{
                'type': 'string',
                'descrition':(
                    '교육장이 위치한 지역명. '
                    '예: 서울, 부산, 대전'
                )
            },
            'room_name': {
                'type': 'string',
                'description': (
                    '조회할 강의실 이름. '
                    '예: A실, B실, 데이터실'
                )
            }
        },
        'required':[
            'location',
            'room_name'
        ]
    }
}

'''
print_title('1. function tool 없이 질문')

interaction_without_tool = client.interactions.create(
    model=MODEL_NAME,
    input=user_question
)

print(interaction_without_tool.output_text)
print()
'''

print_title('2. function tool 사용')

interaction_with_tool = client.interactions.create(
    model=MODEL_NAME,
    input=user_question,
    tools=[
        classroom_function_tool
    ]
)


print_title('3. [output text]')
if interaction_with_tool.output_text:
    print(interaction_with_tool.output_text)
else:
    print('자연어 답변 없음')


steps = interaction_with_tool.steps or []

print_title('interaction steps')
for index, step in enumerate(steps, start=1):
    step_type = getattr(step, 'type', None)
    print(f'[{index}] {step_type}')


function_call_steps = [
    step
    for step in steps
    if getattr(step, 'type', None) == 'function_call'
]

print_title('4. function call 확인')

for index, step in enumerate(function_call_steps, start=1):
    function_name = getattr(step, 'name', None)
    arguments = getattr(step, 'arguments', None)
    call_id = getattr(step, 'call_id', None) or getattr(step, 'id', None) 

    print(f'\n[Function call #{index}]')
    print(f'call_id: {call_id}')
    print(f'function_name: {function_name}')
    print(f'arguments: {arguments}')


print_title('5. 함수 선택 결과')

if not function_call_steps:
    print('function call이 생성되지 않았습니다.')

else:
    first_call = function_call_steps[0]

    selected_name = getattr(first_call, 'name', None)

    selected_arguments = getattr(first_call, 'arguments', None)

    print(f'gemini가 선택한 함수: {selected_name}')
    print(f'gemini가 생성한 arguments: {selected_arguments}')