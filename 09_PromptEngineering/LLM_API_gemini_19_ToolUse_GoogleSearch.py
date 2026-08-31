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

client = genai.Client(api_key= api_key)

MODEL_NAME = "gemini-3.6-flash"

base_question = """
2026년 8월 현재 Python의 최신 안정 버전은 무엇인지 알려줘.

다음 내용을 포함해.
1. 최신 안정 버전
2. 해당 버전의 공식 릴리즈 날짜
3. python 공식 사이트에서 확인되는 핵심 변경사항 3개
4. 수업용 PC에서 바로 업데이트할 때 주의할 점 2개

가능하면 Python 공식 자료를 우선적으로 근거로 사용하라.
"""

search_prompt = """ 
반드시 google search 를 사용해서 최신 정보를 확인한 뒤 답하라.
기억만으로 최신 버전을 단정하지 않는다.
""" + base_question 
# 파라미터를 전달함에 불구하고 프롬프트에도 명시하는 이유는, 확실하게 실행하기 위해서. 안쓸수도 있음.

def print_title(title:str):
    print('\n' + '-' * 80)
    print(title)
    print('-'*80)

print_title('1. google search 없이 실행')

interaction_without_search = client.interactions.create(
    model=MODEL_NAME,
    input=base_question
)

# print(interaction_without_search.output_text)

print_title('2. google search 활성화')

interaction_with_search = client.interactions.create(
    model=MODEL_NAME,
    input=search_prompt,
    tools=[
        {
            'type':'google_search' # LLM이 스스로 tool을 호출하는 기능은 없다.
        }
    ]
)

# print(interaction_with_search.output_text)

steps = interaction_with_search.steps or []

for index, step in enumerate(steps, start=1):
    step_type = getattr(step, 'type', None)
    print(f'\n[{index}] {step_type}')

    if step_type == 'google_search_call':
        arguments = getattr(step, 'arguments', None)
        queries = getattr(arguments, 'queries', None)
        print(f'검색 query: {queries}')

    elif step_type == 'google_search_result':
        result = getattr(step, 'result', None)
        print(f'검색 result 존재: {bool(result)}')

        if result:
            first_result = result[0]
            search_suggestion = getattr(
                first_result,
                'search_suggestions',
                None
            )
            print(f'search suggestion 존재 : {bool(search_suggestion)}')
            # 답변 아래에 "Google에서 검색" 버튼(칩)을 띄울 수 있도록 구글이 제공하는 전용 HTML/CSS 스니펫(칩 버튼) 데이터
    elif step_type == "model_output":
        content_blocks = getattr(
        step,
        'content',
        None
        ) or []

        for block in content_blocks:
            block_type = getattr(block, 'type', None)

            if block_type != "text":
                continue

            text = getattr(block, 'text', None)
            annotations = getattr(block, 'annotations', None)
            print(f'Model Text output:{text}')
            print(f'citation annotation 개수: {len(annotations)}') # 인용한 것들을 명시
            print()

            print_title('annotations 세부 내용')

            # for annotation in annotations:
            #     if annotation.type == "url_citation":
            #         print(f'title : {annotation.title}')
            #         print(f'url : {annotation.url}')
            #         # 전체 응답 텍스트 중 특정 출처(URL 등)의 정보가 인용되거나 적용된 텍스트 구간의 위치(문자 단위 인덱스)
            #         print(f'start_index : {annotation.start_index}')
            #         print(f'end_index : {annotation.end_index}')

print_title("token_usage")
usage = interaction_with_search.usage
if usage:
    print(f'input token: {usage.total_input_tokens}')
    print(f'output token: {usage.total_output_tokens}')
    print(f'thingking token: {usage.total_thought_tokens}')
    print(f'tool use token: {usage.total_tool_use_tokens}') # search는 토큰이 아닌 api횟수로 비용부과됨.
    print(f'total token: {usage.total_tokens}')
