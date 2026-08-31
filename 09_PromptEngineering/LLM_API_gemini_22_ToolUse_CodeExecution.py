import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import csv
import json
from pydantic import BaseModel, Field, ValidationError


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

base_question = """
첫 100개 의 소수를 구한 뒤 다음 값을 계산하라.
1. 소수의 개수
2. 첫번째 소수
3. 100번째 소수
4. 첫 100개 소수의 합
5. 평균
6. 중앙값
7. 처음 10개 소수
8. 마지막 10개 소수

최종 결과를 한국어로 이해하기 쉽게 설명하라.
"""

code_execution_prompt = """
반드시 Code Execution Tool을 사용하여
Python 코드를 실제로 실행한 뒤 답하라.

암산이나 기억으로 결과를 단정하지 않는다.

가능하면 Python 표준 라이브러리를 이용하고, 다음 검증도 코드 안에서 수행한다.

- 실제로 소수가 100개 생성되었는지 확인
- 마지막 값이 정말 100번째 소수 인지 확인
- 계산한 합, 평균, 중앙값을 출력
""" + base_question

interaction_without_code = client.interactions.create(
    model=MODEL_NAME,
    input=base_question
)
print_title('1. code 비활성화')
print(interaction_without_code.output_text)
print()

interaction_with_code = client.interactions.create(
    model=MODEL_NAME,
    input=code_execution_prompt,
    tools=[
        {
            'type':'code_execution'
        }
    ],
    generation_config={
        'thinking_level' : 'medium'
    }
)

print_title('2. code 활성화')
print(interaction_with_code.output_text)
print()

steps = interaction_with_code.steps or []

for index, step in enumerate(steps, start=1):
    step_type = getattr(step, 'type', None)
    print(f'[{index}] {step_type}')

# 2번째 code execution call 스탭을 뜯어보자
print_title('3. code_execution call')

code_call_steps = [
    step for step in steps if getattr(step,'type', None) == 'code_execution_call'
]

for index, step in enumerate(code_call_steps, start=1):
    arguments = getattr(step, 'arguments', None)
    generated_code = getattr(arguments, 'code', None)
    language = getattr(arguments, 'language', None)
    call_id = getattr(step, 'id',  None)

    print(f'\n[code call #{index}]')
    print(f'\ncode_id: {call_id}')
    print(f'\nlanguage: {language}')
    print(f'\n----generate_code----')
    print(generated_code)


code_result_steps = [
    step for step in steps if getattr(step,'type', None) == 'code_execution_result'
]

print_title('4. code_execution result')

for index, step in enumerate(code_result_steps, start=1):
    is_error = getattr(step, 'is_error', None)
    result_text = getattr(step, 'result', None)
    call_id = getattr(step, 'call_id',  None)

    print(f'\n[code call #{index}]')
    print(f'\ncall_id: {call_id}')
    print(f'\nis_error: {is_error}')
    print(f'\n----result_text----')
    print(result_text)

for call_step in code_call_steps:
    call_id = getattr(call_step, 'id', None)

    matching_result = [
        result_step
        for result_step in code_result_steps
        if getattr(result_step, 'call_id', None) == call_id
    ]
    print(f'\ncode call id: {call_id}')
    print(f'연결된 result: {matching_result}')