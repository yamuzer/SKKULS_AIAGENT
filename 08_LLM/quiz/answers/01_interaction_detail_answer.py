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

from pprint import pprint

prompt = """
데이터 분석에서 이상치(outlier)가
평균과 중앙값에 어떤 영향을 줄 수 있는지
간단한 숫자 예시를 포함해서 설명해줘.
"""

interaction = client.interactions.create(
    model=MODEL_NAME,
    input=prompt,
)

print("=" * 80)
print("1. output_text")
print("=" * 80)
print(interaction.output_text)

print("\n" + "=" * 80)
print("2. Interaction 정보")
print("=" * 80)

print("type:", type(interaction))
print("id:", interaction.id)
print("model:", interaction.model)
print("status:", interaction.status)
print("created:", interaction.created)
print("updated:", interaction.updated)

steps = interaction.steps or []

print("\n" + "=" * 80)
print("3. steps")
print("=" * 80)

print("Step count:", len(steps))

for index, step in enumerate(
    steps,
    start=1,
):
    print("\n" + "-" * 80)
    print(f"STEP {index}")
    print("step.type:", getattr(step, "type", None))

    pprint(
        step.model_dump(
            exclude_none=True
        )
    )

print("\n" + "=" * 80)
print("4. model_output text")
print("=" * 80)

for step in steps:

    if getattr(step, "type", None) == "model_output":

        for content in (
            getattr(step, "content", None)
            or []
        ):

            if getattr(content, "type", None) == "text":

                print(
                    content.text
                )

print("\n" + "=" * 80)
print("5. Token Usage")
print("=" * 80)

if interaction.usage:
    print(
        "Input Token:",
        interaction.usage.total_input_tokens,
    )

    print(
        "Output Token:",
        interaction.usage.total_output_tokens,
    )

    print(
        "Thinking Token:",
        interaction.usage.total_thought_tokens,
    )

    print(
        "Total Token:",
        interaction.usage.total_tokens,
    )
else:
    print(
        "Usage 정보를 확인할 수 없습니다."
    )
