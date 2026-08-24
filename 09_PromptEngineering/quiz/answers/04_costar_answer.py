import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"

load_dotenv(
    dotenv_path=ENV_PATH
)

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY를 읽을 수 없습니다."
    )

client = genai.Client(
    api_key=api_key
)

MODEL_NAME = "gemini-3.7-flash"

center_data = """
- 수강생 수: 95명 → 148명
- 질문 대기시간: 6분 → 16분
- 장비 장애 신고: 월 5건 → 14건
- 과제 미제출률: 7% → 13%
- 만족도: 4.7점 → 4.0점
"""

basic_prompt = f"""
다음 교육센터 상황을 분석해줘.

{center_data}
"""

costar_prompt = f"""
[C - Context]

한 교육센터에서
최근 다음과 같은 운영 변화가 있었다.

{center_data}


[O - Objective]

센터장이
현재 가장 시급한 문제와
우선 조치를 판단할 수 있도록 한다.


[S - Style]

짧은 운영 보고서 형태로 작성한다.
수치 중심으로 설명한다.


[T - Tone]

객관적이고 전문적으로 작성한다.
확인되지 않은 원인을 과장하거나 단정하지 않는다.


[A - Audience]

교육센터 센터장


[R - Response]

[핵심 지표]

[가장 시급한 문제]

[근거]

[우선 조치 2개]

[3문장 요약]
"""

basic_result = client.interactions.create(
    model=MODEL_NAME,
    input=basic_prompt,
)

costar_result = client.interactions.create(
    model=MODEL_NAME,
    input=costar_prompt,
)

print("=" * 80)
print("1. 일반 Prompt")
print("=" * 80)
print(
    basic_result.output_text
)

print("\n" + "=" * 80)
print("2. CO-STAR Prompt")
print("=" * 80)
print(
    costar_result.output_text
)
