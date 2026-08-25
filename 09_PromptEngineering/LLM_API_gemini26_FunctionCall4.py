import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError

'''
function call -> call arguments -> 검증
1. dictionary?
2. 필수 key?
3. 올바른 자료형?
4. enum 허용값?
5. 숫자 범위 맞는지?
6. 불필요한 key가 있는지?

-> 검증 완료 -> 실행

'''



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
                'minimum': 0,
                'maximum': 100
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

RoomNameType = Literal[
    'A실',
    'B실',
    'C실',
    '데이터실',
    'AI 실',
    '프로젝트실',
    '세미나실',
    '멀티미디어실'
]


# 정의한 type에 해당하는 데이터가 안들어오면, 리터럴이 exception을 발생시킨다.

class ClassroomInfoArguments(BaseModel):
    model_config = ConfigDict(
        strict=True, 
        extra= 'forbid'  # 그외는 금지
    )
    location: LocationType
    room_name: RoomNameType

class ClassroomsByLocationArguments(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra= 'forbid'
    )
    location : LocationType

class AvaliablePcRoomsArguments(BaseModel):
    model_config = ConfigDict(
        strict=True,# 엄격하게 검사할 건지 10 or "10"
        extra= 'forbid'
    )
    minimum_pc_count : int = Field(
        ge=0,
        le=100
    )

ARGUMENT_MODEL_MAP = {
    'get_classroom_info': ClassroomInfoArguments,
    'get_classrooms_by_location': ClassroomsByLocationArguments,
    'get_available_pc_rooms': AvaliablePcRoomsArguments
}

'''
return 
{
    'valid': True / False,
    'data':검증된 딕셔너리 또는 None
    'errors':오류 목록
}
'''

def validate_function_arguments(
    function_name: str,
    arguments,
) -> dict:
    model_class = ARGUMENT_MODEL_MAP.get(function_name)
    if model_class is None:
        return {
            'valid' : False,
            'data': None,
            'errors': [
                {
                    'type': 'unknown_function',
                    'message': '등록되지 않은 function입니다.'
                }
            ]
        }

    if not isinstance(arguments, dict):
        return {
            'valid' : False,
            'data': None,
            'errors': [
                {
                    'type': 'invalid_arguments_type',
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

def print_validation_result(
    function_name: str,
    arguments
) -> bool:
    print(f'\nfunction: {function_name}')
    print(f'\nraw arguments: {arguments}')

    validation = validate_function_arguments(
        function_name=function_name,
        arguments=arguments
    )
    
    print(f'validation: {validation['valid']}')
    
    if validation['valid']:
        print(f"validated arguments: {validation['data']}")
    else:
        print('\nvalidation erros:')
        for error in validation['errors']:
            print(f'- {error}')
    return validation['valid']

def request_function_call(
    question: str
):
    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=question,
        tools=TOOLS,
        generation_config={
            'tool_choice': {
                'allowed_tools':{
                    'mode': 'any',
                    'tools':[
                        'get_classroom_info',
                        'get_classrooms_by_location',
                        'get_available_pc_rooms'
                    ]
                }
            }
        }
    )

    function_calls = [
        step 
        for step in interaction.steps or []
        if getattr(step, 'type', None) == 'function_call'
    ]

    return (
        interaction,
        function_calls
    )

print_title('1. 정상 argument 검증')
interaction, calls = request_function_call('서울 A실의 좌석 수와 프로젝터 설치 여부를 확인해줘')

for call in calls:
    print_validation_result(
        function_name=call.name,
        arguments=call.arguments
    )


print_title('2. 정상 argument 검증 - 지역 전체')
interaction, calls = request_function_call('부산 교육센터에 있는 전체 강의실 목록을 알려줘.')

for call in calls:
    print_validation_result(
        function_name=call.name,
        arguments=call.arguments
    )

BAD_ARGUMENT_TEST = [
    (
        '필수 Argument 누락',
        'get_classroom_info',
        {
            'location': '서울'
        }
    ),
    (
        'enum에 없는 지역',
        'get_classroom_info',
        {
            'location': '춘천',
            'room_name': 'A실'
        }
    ),
    (
        '잘못된 자료형',
        'get_available_pc_rooms',
        {
            'minimum_pc_count': "30"
        }
    ),
    (
        '불필요한 argument',
        'get_classroom_info',
        {
            'location': '서울',
            'room_name': 'A실',
            'seat_count': 40
        }
    )
]

print_title('잘못된 arguments 검증')

for test_name, function_name, arguments in BAD_ARGUMENT_TEST:
    print(f'\nTest: {test_name}')
    print_validation_result(
        function_name=function_name,
        arguments=arguments
    )