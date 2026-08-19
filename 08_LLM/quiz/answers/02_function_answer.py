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

def ask_gemini(
    prompt: str,
) -> str:

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
    )

    return interaction.output_text


def ask_gemini_with_usage(
    prompt: str,
) -> tuple[str, int | None]:

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
    )

    total_tokens = None

    if interaction.usage:
        total_tokens = (
            interaction.usage.total_tokens
        )

    return (
        interaction.output_text,
        total_tokens,
    )


questions = [
    "정밀도와 재현율의 차이를 설명해줘.",
    "과적합과 과소적합의 차이를 설명해줘.",
    "훈련 데이터와 검증 데이터의 역할 차이를 설명해줘.",
]

for index, question in enumerate(
    questions,
    start=1,
):
    print("\n" + "=" * 80)
    print(f"질문 {index}")
    print("=" * 80)

    result = ask_gemini(
        question
    )

    print(result)


print("\n" + "=" * 80)
print("Usage 포함 함수")
print("=" * 80)

answer, total_tokens = ask_gemini_with_usage(
    """
    머신러닝 모델을 평가할 때
    정확도만 보면 위험할 수 있는 이유를 설명해줘.
    """
)

print(answer)

print(
    "\nTotal Token:",
    total_tokens,
)
