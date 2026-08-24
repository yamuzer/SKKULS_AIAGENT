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

import time

prompt = """
교육센터가 아래 세 개선안 중
하나를 먼저 선택하려 한다.

A. PC 15대 추가 구매
B. 질문 대응 강사 1명 추가
C. 과제 알림 시스템 도입

현재 정보:

- 좌석 부족은 없음
- 질문 대기시간은 6분에서 16분으로 증가
- 장비 장애 신고는 5건에서 14건으로 증가
- 과제 미제출률은 7%에서 13%로 증가
- 만족도는 4.7점에서 4.0점으로 하락

현재 확인된 정보만 사용해서
가장 먼저 시행할 개선안 하나를 추천하고,

1. 선택 이유
2. 기대 효과
3. 현재 정보만으로 알 수 없는 부분

을 설명해줘.
"""


def run_gemini(
    thinking_level: str,
):

    start_time = time.perf_counter()

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        generation_config={
            "thinking_level": thinking_level,
        },
    )

    elapsed_time = (
        time.perf_counter()
        -
        start_time
    )

    print("\n" + "=" * 80)
    print(
        "Thinking Level:",
        thinking_level.upper(),
    )
    print("=" * 80)

    print(
        interaction.output_text
    )

    thought_tokens = None
    total_tokens = None

    if interaction.usage:
        thought_tokens = (
            interaction.usage.total_thought_tokens
        )

        total_tokens = (
            interaction.usage.total_tokens
        )

    print(
        "\n응답 시간:",
        round(elapsed_time, 2),
        "초",
    )

    print(
        "Thought Token:",
        thought_tokens,
    )

    print(
        "Total Token:",
        total_tokens,
    )

    return {
        "level": thinking_level,
        "interaction": interaction,
        "elapsed": elapsed_time,
        "thought_tokens": thought_tokens,
        "total_tokens": total_tokens,
    }


results = [
    run_gemini("low"),
    run_gemini("medium"),
    run_gemini("high"),
]

print("\n" + "=" * 80)
print("최종 비교")
print("=" * 80)

for result in results:
    print(
        result["level"].upper(),
        "| time:",
        round(result["elapsed"], 2),
        "| thought:",
        result["thought_tokens"],
        "| total:",
        result["total_tokens"],
    )
