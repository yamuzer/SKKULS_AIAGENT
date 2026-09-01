import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
COURSE_CSV_PATH = BASE_DIR / "day3" / "data" / "course_requirements.csv"
CLASSROOM_CSV_PATH = BASE_DIR / "day3" / "data" / "classroom_info.csv"

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

def load_csv(
    csv_path: Path
) -> list[dict]:

    with csv_path.open(
        mode='r',
        encoding='utf-8-sig',
        newline=''
    )as csv_file:

        return list(csv.DictReader(csv_file))
    

CLASSROOM_DATA = load_csv(CLASSROOM_CSV_PATH)
COURSE_DATA = load_csv(COURSE_CSV_PATH)

for course in COURSE_DATA:
    course['minimum_pc_count'] = int(course['minimum_pc_count'])
    course['expected_students'] = int(course['expected_students'])


for classroom in CLASSROOM_DATA:
    classroom['floor'] = int(classroom['floor'])
    classroom['seat_count'] = int(classroom['seat_count'])
    classroom['pc_count'] = int(classroom['pc_count'])


def normalize_text(value: str) -> str:
    return value.strip()

def yn_to_bool(value: str) -> bool:
    return value.strip().upper() == 'Y'

def convert_classroom(classroom: dict) -> dict:

    return {
        'location': classroom['location'],
        'building': classroom['building'],
        'room_name': classroom['room_name'],
        'floor': classroom['floor'],
        'purpose': classroom['purpose'],
        'seat_count': classroom['seat_count'],
        'projector': yn_to_bool(classroom['projector']),
        'pc_count': classroom['pc_count'],
        'smart_board': yn_to_bool(classroom['smart_board']),
        'wifi': yn_to_bool(classroom['wifi']),
        'accessibility': yn_to_bool(classroom['accessibility']),

    }

'''
get_course_requirements
과정명 -> 운영 지역 / 최소 pc 수량
'''

def get_course_requirements(
        course_name: str
) -> dict:
    for course in COURSE_DATA:
        if course['course_name'] == course_name:

            return{
                'success': True,
                'course_name': course['course_name'],
                'location': course['location'],
                'minimum_pc_count': course['minimum_pc_count'],
                'expected_students': course['expected_students'],
                'preferred_purpose': course['preferred_purpose'],
                'note': course['note']
            }
    return {
        'success': False,
        'message': '과정 정보를 찾을 수 없습니다.',
        'course_name': course_name
    }



def find_pc_rooms(
        location: str,
        minimum_pc_count: int
) -> dict:
    
    matched = [
        convert_classroom(classroom)
        for classroom in CLASSROOM_DATA
        if (classroom['location'] == location and classroom['pc_count'] >= minimum_pc_count)
    ]

    matched.sort(
        key=lambda item: (item['pc_count'], item['seat_count']),
        reverse=True
    )

    return {
        'success': bool(matched),
        'location': location,
        'minimum_pc_count': minimum_pc_count,
        'count': len(matched),
        'recommended_room': (
            matched[0]
            if matched else None
        ),
        'rooms': matched
    }


FUNCTION_MAP = {
    'get_course_requirements': get_course_requirements,
    'find_pc_rooms': find_pc_rooms
}

COURSE_NAMES = [
    'Python 기초',
    '웹 백엔드 실무',
    '데이터분석 실무',
    'AI 모델링',
    'RAG 서비스',
    'DB 실무',
    '클라우드 데이터',
    '멀티모달 AI',
    '비전 AI'
]


get_course_requirements_tool = {
    'type': 'function',
    'name': 'get_course_requirements',
    'description':(
        '교육 과정 이름을 입력 받아 그 과정의 운영 지역, 필요한 최소 PC 수량, 예상 학생 수, '
        '선호 강의실 용도를 조회합니다. 과정 이름으로 강의실 추천을 요청 받으면 반드시 이 Function을 먼저 호출합니다.'
    ),
    'parameters':{
        'type': 'object',
        'properties':{
            'course_name':{
                'type': 'string',
                'descrition':(
                    '교육 과정 이름 '
                ),
                'enum':COURSE_NAMES
            }
        },
        'required':[
            'course_name'
        ]
    }
}



find_pc_rooms_tool = {
    'type': 'function',
    'name': 'find_pc_rooms',
    'description':(
        '특정 지역에서 최소 PC 수량 조건을 만족하는 강의실을 검색합니다. '
        '과정 기반 추천에서 location과 minimum_pc_count를 임의로 추측하지 말고 '
        'get_course_requirements Result에서 받은 실제 값을 사용합니다.'
    ),
    'parameters':{
        'type': 'object',
        'properties': {
            'location':{
                'type': 'string',
                'description': '교육센터 지역',
                'enum': [
                    '서울','부산','대전','대구','광주','인천','수원','성남','울산','제주'
                ]
            },
            'minimum_pc_count':{
                'type': 'integer',
                'description': '필요한 최소 PC 수량',
                'minimum': 0,
                'maximum': 100
            }
        },
        'required':[
            'location',
            'minimum_pc_count'
        ]
    }
}


TOOLS = [
    get_course_requirements_tool,
    find_pc_rooms_tool
]

SYSTEM_INSTRUCTION = """
당신은 교육센터 강의실 추천 도우미입니다.


과정 이름을 기준으로 강의실 추천을 요청받으면 반드시 다음 순서를 지키세요.

1. 먼저 get_course_requirements를 호출하세요.
2. 그 Function Result에서 실제 location과 minimum_pc_count를 확인하세요.
3. location과 minimum_pc_count를 추측하거나 임의의 만들지 마세요.
4. 첫 Function Result를 받은 뒤에만 find_pc_rooms를 호출하세요.
5. find_pc_rooms Result를 받은 뒤 recommended_room을 중심으로 최종 답변을 만드세요.

Function Result에 없는 정보는 만들어내지 마세요.
"""


CourseNameType = Literal[
    'Python 기초',
    '웹 백엔드 실무',
    '데이터분석 실무',
    'AI 모델링',
    'RAG 서비스',
    'DB 실무',
    '클라우드 데이터',
    '멀티모달 AI',
    '비전 AI'
]

LocationType = Literal[
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

class CourseRequirementsArguments(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra='forbid'
    )

    course_name : CourseNameType


class FindPcRoomsArguments(BaseModel):

    model_config = ConfigDict(
        strict=True,
        extra='forbid'
    )

    location: LocationType

    minimum_pc_count: int = Field(
        ge=0,
        le=100
    )


ARGUMENT_MODEL_MAP = {
    'get_course_requirements': CourseRequirementsArguments,
    'find_pc_rooms': FindPcRoomsArguments,
}


def validate_function_arguments(
    function_name: str,
    arguments
) -> dict:

    model_class = ARGUMENT_MODEL_MAP.get(function_name)

    if model_class is None:
        return {
            'valid': False,
            'data': None,
            'errors':[
                {
                    'message':'등록되지 않은 function입니다.'
                }
            ]
        }

    if not isinstance(arguments, dict):
        return {
            'valid': False,
            'data': None,
            'errors': [
                {
                    'message': 'arguments는 dict여야 합니다.'
                }
            ]
        }

    try:
        validated = model_class.model_validate(arguments)

        return {
            'valid': True,
            'data': validated.model_dump(),
            'errors': []
        }

    except ValidationError as error:
        return {
            'valid': False,
            'data': None,
            'errors': error.errors()
        }



def execute_function(
    function_name: str,
    validated_arguments: dict
) -> dict:

    python_function = FUNCTION_MAP.get(function_name)

    if python_function is None:
        return {
            'success': False,
            'error': (
                '실행할 Python Function을 찾을 수 없습니다.'
            )
        }

    try:
        return python_function(**validated_arguments)

    except Exception as error:
        return {
            'success': False,
            'error_type': type(error).__name__,
            'error': str(error)
        }


def build_function_result_input(
    call,
    function_result: dict
) -> dict:

    return {
        'type': 'function_result',
        'name': call.name,
        'call_id': call.id,
        'result':[
            {
                'type': 'text',
                'text': json.dumps(
                    function_result,
                    ensure_ascii=False
                )
            }
        ]
    }


def get_function_calls(
        interaction
) -> list:
    return [
        step
        for step in interaction.steps or []
        if getattr(step, 'type', None) == 'function_call'
    ]


def run_sequential_workflow(
        question: str,
        max_rounds: int = 5
) -> str:

    print_title(f'사용자 질문 : {question}')

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=question,
        system_instruction=SYSTEM_INSTRUCTION,
        tools=TOOLS,
        generation_config={
            'tool_choice': 'auto'
        }
    )

    for round_number in range(1, max_rounds + 1):
        print(f'ROUND {round_number}')
        print(f'interaction.id: {interaction.id}')
        print(f'status: {interaction.status}')

        function_calls = get_function_calls(interaction=interaction)

        if not function_calls:
            final_text = interaction.output_text or '최종 답변이 생성되지 않았습니다.'
            print('workflow 완료')
            print('='*80)
            print(final_text)

            return final_text

        function_results = []

        for call_index, call in enumerate(function_calls, start=1):
            print(f'function call #{call_index}')
            print(f'call.id: {call.id}')
            print(f'call.name: {call.name}')
            print(f'call.arguments: {call.arguments}')

            validation = validate_function_arguments(
                function_name=call.name,
                arguments=call.arguments
            )

            print(f'Validation: {validation["valid"]}')

            if not validation['valid']:
                execution_result = {
                    'success': False,
                    'error_type': 'argument_validation_error',
                    'errors': validation['errors']
                }

            else:
                execution_result = execute_function(
                    function_name=call.name,
                    validated_arguments=validation['data']
                )

            print('\n[function result]')
            print(
                json.dumps(
                    execution_result,
                    ensure_ascii=False,
                    indent=2
                )
            )

            function_results.append(
                build_function_result_input(
                    call=call,
                    function_result=execution_result
                )
            )

        interaction = client.interactions.create(
            model=MODEL_NAME,
            previous_interaction_id=interaction.id,
            input=function_results,
            system_instruction=SYSTEM_INSTRUCTION,
            tools=TOOLS,
            generation_config={
                'tool_choice': 'auto'
            }
        )

    raise RuntimeError(
        f'Sequential Function Calling이 {max_rounds} Round 안에 끝나지 않았습니다.'
    )


run_sequential_workflow(
    '데이터분석 실무 과정이 열리는 지역과 필요한 PC스를 먼저 확인한 다음, ' \
    '그 조건을 만족하는 강의실 중 PC가 가장 많은 곳을 추천해줘.'
)

