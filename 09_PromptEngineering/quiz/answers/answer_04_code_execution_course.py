import base64
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

DATA_PATH = (
    BASE_DIR
    / "data"
    / "course_activity.csv"
)

OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.6-flash"


def print_title(title: str):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# ============================================================
# 1. CSV를 Base64 inline document로 준비
# ============================================================

csv_bytes = DATA_PATH.read_bytes()

csv_base64 = base64.b64encode(
    csv_bytes
).decode("utf-8")


print_title("1. CSV Inline Input")

print("파일:", DATA_PATH.name)
print("파일 크기(byte):", len(csv_bytes))
print("mime_type: text/csv")


# ============================================================
# 2. 분석 Prompt
# ============================================================

prompt = """
첨부된 course_activity.csv를
반드시 Code Execution Tool의 Python 코드로 실제 분석하라.

CSV 파일은 첨부된 document 입력을 직접 읽어서 분석한다.

반드시 계산할 항목:

1. 전체 행 수

2. 고유 student_id 수

3. activity_date의
   - 최소 날짜
   - 최대 날짜

4. 중복
   - 완전히 동일한 중복 행 수
   - activity_id 기준 중복 추가 행 수

5. 모든 컬럼의 결측치 수

6. 다음 컬럼의 기본 통계
   - study_minutes
   - completion_rate
   - quiz_score

7. course_name별 평균
   - study_minutes
   - completion_rate
   - quiz_score

8. 전체 dropout_flag 비율

9. 평균 completion_rate가 높은 과정 상위 3개

10. study_minutes와 quiz_score의 Pearson 상관계수

11. activity_date를 datetime으로 변환하고
    YYYY-MM month 컬럼을 만든 뒤
    월별 평균
    - study_minutes
    - quiz_score
    를 날짜순으로 출력

12. 다음 이상치 개수
    - study_minutes > 600
    - quiz_score > 100
    - completion_rate > 1
    - estimated_cost_krw < 0

중요 규칙:
- 반드시 Code Execution Tool을 사용한다.
- pandas를 사용해 실제 계산한다.
- 숫자를 추측하지 않는다.
- 결측치를 무조건 0으로 변경하지 않는다.
- 이상값을 임의로 삭제하지 않는다.
- 핵심 계산 결과를 print()로 출력한다.
- 상관관계를 인과관계라고 단정하지 않는다.
- 최종 설명은 한국어로 작성한다.
"""


# ============================================================
# 3. Interactions API + Code Execution
# ============================================================

print_title("2. Gemini Code Execution")

interaction = client.interactions.create(
    model=MODEL_NAME,
    input=[
        {
            "type": "text",
            "text": prompt,
        },
        {
            "type": "document",
            "data": csv_base64,
            "mime_type": "text/csv",
        },
    ],
    tools=[
        {
            "type": "code_execution"
        }
    ],
    generation_config={
        "thinking_level": "medium"
    },
)


print_title("3. Final Answer")
print(interaction.output_text)


# ============================================================
# 4. Step 확인
# ============================================================

steps = interaction.steps or []

print_title("4. Interaction Steps")

for index, step in enumerate(
    steps,
    start=1,
):
    print(
        f"[{index}]",
        getattr(
            step,
            "type",
            None,
        ),
    )


# ============================================================
# 5. code_execution_call
# ============================================================

code_call_steps = [
    step
    for step in steps
    if getattr(
        step,
        "type",
        None,
    ) == "code_execution_call"
]


print_title("5. Generated Python Code")

for index, step in enumerate(
    code_call_steps,
    start=1,
):

    arguments = getattr(
        step,
        "arguments",
        None,
    )

    call_id = getattr(
        step,
        "id",
        None,
    )

    language = getattr(
        arguments,
        "language",
        None,
    )

    generated_code = getattr(
        arguments,
        "code",
        None,
    )

    print()
    print(
        f"[Code Call #{index}]"
    )

    print("call_id:", call_id)
    print("language:", language)

    print()
    print("----- generated code -----")
    print(generated_code)


# ============================================================
# 6. code_execution_result
# ============================================================

code_result_steps = [
    step
    for step in steps
    if getattr(
        step,
        "type",
        None,
    ) == "code_execution_result"
]


print_title("6. Code Execution Result")

for index, step in enumerate(
    code_result_steps,
    start=1,
):

    call_id = getattr(
        step,
        "call_id",
        None,
    )

    result_text = getattr(
        step,
        "result",
        None,
    )

    is_error = getattr(
        step,
        "is_error",
        None,
    )

    print()
    print(
        f"[Code Result #{index}]"
    )

    print("call_id:", call_id)
    print("is_error:", is_error)

    print()
    print("----- execution result -----")
    print(result_text)


# ============================================================
# 7. call.id와 result.call_id 연결 + Audit CSV
# ============================================================

audit_rows = []


print_title("7. Call / Result 연결")

for call_index, call_step in enumerate(
    code_call_steps,
    start=1,
):

    arguments = getattr(
        call_step,
        "arguments",
        None,
    )

    call_id = getattr(
        call_step,
        "id",
        None,
    )

    language = getattr(
        arguments,
        "language",
        None,
    )

    generated_code = getattr(
        arguments,
        "code",
        None,
    )

    matching_results = [
        result_step
        for result_step in code_result_steps
        if getattr(
            result_step,
            "call_id",
            None,
        ) == call_id
    ]

    print()
    print("code call id:", call_id)
    print(
        "연결된 result 개수:",
        len(matching_results),
    )

    if not matching_results:

        audit_rows.append(
            {
                "call_index": call_index,
                "call_id": call_id or "",
                "language": language or "",
                "is_error": "",
                "generated_code": (
                    generated_code or ""
                ),
                "execution_result": (
                    "NO MATCHING RESULT"
                ),
            }
        )

        continue

    for result_step in matching_results:

        result_text = getattr(
            result_step,
            "result",
            None,
        )

        is_error = getattr(
            result_step,
            "is_error",
            None,
        )

        print(
            "result.call_id:",
            getattr(
                result_step,
                "call_id",
                None,
            ),
        )

        print(
            "is_error:",
            is_error,
        )

        audit_rows.append(
            {
                "call_index": call_index,
                "call_id": call_id or "",
                "language": language or "",
                "is_error": is_error,
                "generated_code": (
                    generated_code or ""
                ),
                "execution_result": str(
                    result_text or ""
                ),
            }
        )


audit_path = (
    OUTPUT_DIR
    / "course_code_audit.csv"
)

with audit_path.open(
    "w",
    newline="",
    encoding="utf-8-sig",
) as csv_file:

    fieldnames = [
        "call_index",
        "call_id",
        "language",
        "is_error",
        "generated_code",
        "execution_result",
    ]

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(
        audit_rows
    )


print_title("8. Audit CSV 저장")
print("저장 경로:", audit_path)


if not code_call_steps:
    raise RuntimeError(
        "Code Execution Tool이 실행되지 않았습니다."
    )

if not code_result_steps:
    raise RuntimeError(
        "Code Execution 결과가 없습니다."
    )
