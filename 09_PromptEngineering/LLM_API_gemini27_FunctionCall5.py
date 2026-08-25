import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
CSV_PATH = BASE_DIR / "data" / "classroom_info.csv"


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

def load_classroom_data(
    csv_path: Path
) -> list[dict]:
    data = []
    with csv_path.open(
        mode='r',
        encoding='utf-8-sig',
        newline=''
    ) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            row['floor'] = int(row['floor'])
            row['seat_count'] = int(row['seat_count'])
            row['pc_count'] = int(row['pc_count'])
            data.append(row)
    return data

CLASSROOM_DATA = load_classroom_data(CSV_PATH)
# print(CLASSROOM_DATA)

def normalize_text(value: str)-> str:
    return value.strip()

def yn_to_bool(value: str) -> bool:
    return value.strip().upper() == 'Y'

def convert_classroom(classroom: dict) -> dict:
    return {
        'location' : classroom['location'],
        'building' : classroom['building'],
        'room_name' : classroom['room_name'],
        'floor' : classroom['floor'],
        'purpose' : classroom['purpose'],
        'projector' : yn_to_bool(classroom['projector']),
        'pc_count' : classroom['pc_count'],
        'smart_board' : classroom['smart_board'],
        'wifi' : yn_to_bool(classroom['wifi']),
        'accessibility' : yn_to_bool(classroom['accessibility']),
    }

def get_classroom_info(
    location: str,
    room_name: str
)-> dict:
    location = normalize_text(location)
    room_name = normalize_text(room_name)
    for classroom in CLASSROOM_DATA:
        if (classroom['location'] == location and classroom['room_name' == room_name]):
            return {
                'success' : True,
                'data' : convert_classroom(classroom)
            }
    
    return {
        'success': False,
        'message': (
            '조건에 맞는 강의실을 찾을 수 없습니다.'
        ),
        'query':{
            'location':location,
            'room_name' : room_name
        }
    }

def get_classrooms_by_location(location: str)-> dict:
    location = normalize_text(location)
    matched = [
        convert_classroom(classroom)
        for classroom in CLASSROOM_DATA
        if classroom['location'] == location
    ]

    return {
        'success': bool(matched),
        'location': location,
        'count': len(matched),
        'data': matched
    }


def get_available_pc_rooms(minimum_pc_count:int)-> dict:
    matched = [
        convert_classroom(classroom)
        for classroom in CLASSROOM_DATA
        if classroom['[pc_count]'] >= minimum_pc_count
    ]

    matched.sort(
        key=lambda item: (item['pc_count'], item['seat_count']),
        reverse = True
    )
    
    return {
        'success': True,
        'minimum_pc_count': minimum_pc_count,
        'count': len(matched),
        'data': matched
    }

FUNCTION_MAP = {
    'get_classroom_info': get_classroom_info,
    'get_classrooms_by_location' : get_classrooms_by_location,
    'get_available_pc_rooms' : get_available_pc_rooms
}    


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

def execute_function(
    function_name: str,
    validated_arguments: dict
) -> dict:
    python_function = FUNCTION_MAP.GET(function_name)
    return {
        'success' :  False,
        'error' : (
            '실행할 Python Function을 찾을 수 없습니다.'
        )
    }
    try:
        return python_function(**validated_arguments)

    except Exception as error:
        return {
            'success' : False,
            'error_type' : type(error).__name__,
            'error': str(error)
        }

'''
function call result -> llm 전달 할 때
{
    'type' : 'function_reulst',
    'name' : call.name,
    'call_id' : call.id,
    'result' : [
        {
            'type':'text',
            'text': json.dumps(
                function_result
                )
    }]
}
'''

def build_function_result_input(
    call,
    function_result: dict
) -> dict:
    return {
        'type': 'function_result',
        'name' : call.name,
        'call_id' : call.id,
        'result' : [
            {
                'type':'text',
                'text': json.dumps(
                    function_result,
                    ensure_ascii=False
                )
            }
        ]
    }

def process_question(
    question:str
) -> None:
    print_title(f'사용자 질문: {question}')
    first_interaction = client.interactions.create(
        model=MODEL_NAME,
        input=question,
        tools=TOOLS,
        generation_config={
            'tool_choice' : 'any'
        }
    )
    print('\n[Turn 1]')
    print(f'interaction.id: {first_interaction.id}')
    print(f'status: {first_interaction.status}')

    function_calls = [
        step
        for step in first_interaction.steps or []
        if getattr(step, 'type', None) == 'function_call'
    ]

    if not function_calls:
        print('function call이 없습니다.')
        return
    
    function_result_inputs = []

    for index, call in enumerate(function_calls, start=1):
        print(f'\nfunction call : {index}')
        print(f'call.id: {call.id}')
        print(f'call.name: {call.name}')
        print(f'call.arguments: {call.arguments}')

        validation = validate_function_arguments(
            function_name = call.name,
            arguments=call.arguments
        )

        print(f'\nvalidation: {validation['valid']}')

        if not validation['valid']:
            print('function 실행을 차단합니다.')

            for error in validation['errors']:
                print(f'- {error}')
            
            continue

        validated_arguments = validation['data']

        function_result = execute_function(
            function_name=call.name,
            validated_arguments=validated_arguments
        )

        print(f'\n[실제 python function result]')
        print(json.dumps(
            function_result = function_result,
            ensure_ascii=False, # 유니코드로 변환하지 않고 원래 글자 그대로 출력
            indent=2 # 2칸 들여쓰기
        ))



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
