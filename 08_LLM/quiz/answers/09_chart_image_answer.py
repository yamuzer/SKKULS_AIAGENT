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

CHART_PATH = (
    DATA_DIR
    / "weekly_support_tickets.png"
)

if not CHART_PATH.exists():
    raise FileNotFoundError(
        f"그래프를 찾을 수 없습니다: {CHART_PATH}"
    )

uploaded_chart = client.files.upload(
    file=str(CHART_PATH)
)

prompt = """
첨부된 그래프 이미지를 분석해줘.

다음 순서로 답해줘.

1. X축의 의미
2. Y축의 의미
3. 1주차 값
4. 8주차 값
5. 16주차 값
6. 전체 추세
7. 증가가 두드러지는 구간
8. 일시적으로 감소한 구간이 있는지
9. 그래프만으로 알 수 없는 원인 3개

규칙:

- 그래프에서 정확한 값을 읽기 어려우면
  "약" 또는 "대략"이라고 표현해줘.

- 그래프에 표시되지 않은
  실제 원인을 추측하지 마.

마지막에는
그래프의 핵심 메시지를
3문장 이내로 요약해줘.
"""

interaction = client.interactions.create(
    model=MODEL_NAME,
    input=[
        {
            "type": "text",
            "text": prompt,
        },
        {
            "type": "image",
            "uri": uploaded_chart.uri,
            "mime_type": uploaded_chart.mime_type,
        },
    ],
)

print("=" * 80)
print("그래프 분석 결과")
print("=" * 80)

print(
    interaction.output_text
)

if interaction.usage:
    print("\n" + "=" * 80)
    print("Token Usage")
    print("=" * 80)

    print(
        "Input:",
        interaction.usage.total_input_tokens,
    )

    print(
        "Output:",
        interaction.usage.total_output_tokens,
    )

    print(
        "Thought:",
        interaction.usage.total_thought_tokens,
    )

    print(
        "Total:",
        interaction.usage.total_tokens,
    )

client.files.delete(
    name=uploaded_chart.name
)

print(
    "\n업로드한 그래프를 삭제했습니다."
)
