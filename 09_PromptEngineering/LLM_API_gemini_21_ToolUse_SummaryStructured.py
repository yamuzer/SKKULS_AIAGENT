import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import csv
import json
from pydantic import BaseModel, Field, ValidationError


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

JSON_OUTPUT_PATH = BASE_DIR / 'data' / 'python_version_comparison.json'
OUTPUT_CSV_PATH = BASE_DIR / 'data' / 'python_version_comparison.csv'

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.7-flash"

PYTHON_313_URL = "https://docs.python.org/3.13/whatsnew/3,13.html"
PYTHON_314_URL = 'https://docs.python.org/3.14/whatsnew/3.14.html'

def print_title(title:str):
    print('\n' + '-' * 80)
    print(title)
    print('-' * 80)
    print()

class PythonVersionSummary(BaseModel):
    version : str = Field(
        description="문서가 설명하는 Python 버전"
    )
    release_date : str = Field(
        description="What's New 문서에 직접 적힌 공식 릴리즈 날짜"
    )
    release_highlights : list[str] = Field(
        description="Summary - Release Highlight에서 중요하게 소개된 변화"
    )
    free_threaded : str = Field(
        description="해당 버전에서 free-threaded python의 상태와 의미"
    )
    interpreter_or_concurrency_change: str = Field(
        description="multiple interpreters, concurrency, parallelism과 관련하여 문서에서 직접 확인되는 핵심 변화"
    )
    standard_library_changes: list[str] = Field(
        description="비교에 중요한 표준 라이브러리 변화"
    )


class PythonVersionComparison(BaseModel):
    source_urls: list[str] = Field(
        description="실제로 비교에 사용한 두 공식 URL"
    )
    python_313 : PythonVersionSummary = Field(
        description="python 3.13 공식 Whats New 분석"
    )
    python_314 : PythonVersionSummary = Field(
        description="python 3.14 공식 Whats New 분석"
    )
    free_threaded_evolution: str = Field(
        description="3.13에서 3.14로 free_threaded 지원 상태가 어떻게 변했는지"
    )
    major_differences : list[str] = Field(
        description="두 버전 사이에서 확인되는 핵심 차이"
    )
    common_themes: list[str] = Field(
        description="두 문서에서 공통적으로 나타나는 발전 방향 또는 주제"
    )
    update_checkpoints: list[str] = Field(
        description="3.13에서 3.14로 업그레이드 할 때 두 문서에 근거해 확인하면 좋은 항목"
    )

prompt = f"""
다음 두 개의 Python 공식 What's New 문서를 URL Context Tool로 모두 직접 읽고 비교하라.

[URL A - Python 3.13]
{PYTHON_313_URL}

[URL B - Python 3.14]
{PYTHON_314_URL}

목표 : 
각 문서를 독립적으로 읽은 뒤 같은 기준으로 정보를 추출하고, 마지막에 두문 서를 서로 비교한다.

반드시 확인할 항목:
1. 각 버전의 공식 릴리즈 날짜
2. 각 문서의 Summary - Release Highlights에서 중요하게 소개하는 변화
3. free-threaded Python 의 상태
4. multiple interpreters, concurrency, parallelism과 관련된 변화
5. 두 버전의 주요 차이
6. Python 3.13에서 Python 3.14로 넘어가면서 free-threaded 지원 상태가 어떻게 발전했는지
7. 비교에 중요한 표준 라이브러리 변화
8. 두 버전에 공통적으로 나타나는 Python 의 발전 방향
9. Python 3.13 사용자가 Python 3.14로 업그레이드할 때 확인하면 좋은 항목

중요 규칙:
- Google Searchs를 사용하지 않는다.
- 반드시 제공한 두 URL의 내용만 사용한다.
- URL A의 내용을 URL B의 내용처럼 섞어서 기록하지 않는다.
- 한 문서에 없는 사실을 다른 문서에서 가져와 그 문서의 사실인 것처럼 쓰지 않는다.
- free-threaded상태에서 experimental과 official supported를 명확히 구분한다.
- 페이지에서 확인 할수 없는 정보는 추측하지 않는다.
- 같은 내용을 불필요하게 반복하지 않는다.
- Markdown 설명을 추가하지 않는다.
- 최종 결과는 지정된 strutured output만 반환한다.
"""

def request_comparison():
    return client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        tools=[
            {
                'type': 'url_context'
            }
        ],
        generation_config={

            'thinking_level': 'medium'
        },
        response_format={
            'type': 'text',
            'mime_type': 'application/json',
            'schema': PythonVersionComparison.model_json_schema()
            
        }
    )

interaction = request_comparison()
raw_json = interaction.output_text
print_title('1. raw structured output')
print(raw_json)

try: 
    result = PythonVersionComparison.model_validate_json(raw_json)
except ValidationError as error:
    print(error)
    interation = request_comparison()