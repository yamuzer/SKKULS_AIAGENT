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

prompt_1 = """
다음 학습 계획을 기억해줘.

수강생 이름은 박서준이고,
현재 SQL을 공부하고 있으며,
다음 학습 목표는 Python 데이터 분석이고,
하루 학습 가능 시간은 2시간이야.
"""

interaction_1 = client.interactions.create(
    model=MODEL_NAME,
    input=prompt_1,
)

prompt_2 = """
현재 공부하고 있다고 말한 과목은?
"""

interaction_2 = client.interactions.create(
    model=MODEL_NAME,
    input=prompt_2,
    previous_interaction_id=interaction_1.id,
)

prompt_3 = """
다음 학습 목표는 무엇이라고 했지?
"""

interaction_3 = client.interactions.create(
    model=MODEL_NAME,
    input=prompt_3,
    previous_interaction_id=interaction_2.id,
)

prompt_4 = """
앞의 정보를 기준으로
하루 2시간짜리 학습 순서를
4단계로 제안해줘.
"""

interaction_4 = client.interactions.create(
    model=MODEL_NAME,
    input=prompt_4,
    previous_interaction_id=interaction_3.id,
)

interactions = [
    interaction_1,
    interaction_2,
    interaction_3,
    interaction_4,
]

for index, interaction in enumerate(
    interactions,
    start=1,
):
    print("\n" + "=" * 80)
    print(f"Interaction {index}")
    print("=" * 80)

    print(
        interaction.output_text
    )

print("\n" + "=" * 80)
print("Interaction ID")
print("=" * 80)

for index, interaction in enumerate(
    interactions,
    start=1,
):
    print(
        f"{index}:",
        interaction.id,
    )
