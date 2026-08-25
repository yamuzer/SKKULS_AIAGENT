import csv
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field, ValidationError


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

URL_FILE_PATH = (
    BASE_DIR
    / "data"
    / "official_urls.csv"
)

OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.7-flash"


def print_title(title: str):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# ============================================================
# Pydantic Model
# ============================================================

class OldVersionSummary(BaseModel):

    version: str = Field(
        description="이전 pandas 버전"
    )

    release_date: str = Field(
        description="공식 릴리스 날짜"
    )

    highlights: list[str] = Field(
        description="pandas 3.0.0 핵심 변화"
    )

    compatibility_notes: list[str] = Field(
        description="호환성 및 마이그레이션 주의사항"
    )


class NewVersionSummary(BaseModel):

    version: str = Field(
        description="새 pandas 버전"
    )

    release_date: str = Field(
        description="공식 릴리스 날짜"
    )

    highlights: list[str] = Field(
        description="pandas 3.0.5 문서의 핵심 내용"
    )

    bugfix_or_regression_topics: list[str] = Field(
        description="bugfix 또는 regression 관련 주요 주제"
    )


class PandasVersionComparison(BaseModel):

    source_urls: list[str]

    old_version: OldVersionSummary

    new_version: NewVersionSummary

    major_differences: list[str]

    upgrade_checkpoints: list[str]


# ============================================================
# official_urls.csv에서 URL 읽기
# ============================================================

url_map = {}

with URL_FILE_PATH.open(
    "r",
    newline="",
    encoding="utf-8-sig",
) as csv_file:

    reader = csv.DictReader(csv_file)

    for row in reader:
        url_map[row["name"]] = row["url"]


OLD_URL = url_map.get(
    "pandas_3_0_0"
)

NEW_URL = url_map.get(
    "pandas_3_0_5"
)


if not OLD_URL or not NEW_URL:
    raise ValueError(
        "official_urls.csv에서 pandas 3.0.0/3.0.5 URL을 찾지 못했습니다."
    )


prompt = f"""
다음 두 pandas 공식 릴리스 문서를
URL Context Tool로 직접 읽고 비교하라.

[OLD - pandas 3.0.0]
{OLD_URL}

[NEW - pandas 3.0.5]
{NEW_URL}

각 문서를 독립적으로 읽은 뒤 비교한다.

반드시 다음을 구분해서 작성한다.

1. pandas 3.0.0
   - 버전
   - 공식 릴리스 날짜
   - 주요 변화
   - 호환성/마이그레이션 주의사항

2. pandas 3.0.5
   - 버전
   - 공식 릴리스 날짜
   - 문서의 주요 내용
   - bugfix 또는 regression 관련 주제

3. 두 문서의 주요 차이

4. 3.0.0에서 3.0.5 계열을 사용할 때
   확인하면 좋은 업그레이드 체크포인트

중요 규칙:
- Google Search를 사용하지 않는다.
- 반드시 제공한 두 URL의 내용만 사용한다.
- 3.0.0 사실과 3.0.5 사실을 서로 섞지 않는다.
- 문서에 없는 사실은 추측하지 않는다.
- Markdown 설명을 추가하지 않는다.
- 최종 결과는 지정된 Structured Output만 반환한다.
"""


def request_comparison():

    return client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        tools=[
            {
                "type": "url_context"
            }
        ],
        generation_config={
            "thinking_level": "medium"
        },
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": (
                PandasVersionComparison
                .model_json_schema()
            ),
        },
    )


result = None
raw_json = None
last_error = None


# ============================================================
# 최초 요청 + 검증 실패 시 최대 1회 재요청
# ============================================================

for attempt in range(
    1,
    3,
):

    print_title(
        f"Request Attempt {attempt}"
    )

    interaction = request_comparison()

    raw_json = interaction.output_text

    print(raw_json)

    try:
        result = (
            PandasVersionComparison
            .model_validate_json(
                raw_json
            )
        )

        break

    except ValidationError as error:

        last_error = error

        print()
        print("ValidationError")
        print(error)


if result is None:
    raise RuntimeError(
        f"Structured Output 검증 실패: {last_error}"
    )


# ============================================================
# JSON 저장
# ============================================================

json_path = (
    OUTPUT_DIR
    / "pandas_version_comparison.json"
)

json_path.write_text(
    json.dumps(
        result.model_dump(),
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# 핵심 비교 CSV 저장
# ============================================================

csv_rows = [
    {
        "version_type": "old_version",
        "version": result.old_version.version,
        "release_date": (
            result.old_version.release_date
        ),
        "highlights": " | ".join(
            result.old_version.highlights
        ),
        "notes": " | ".join(
            result.old_version.compatibility_notes
        ),
    },
    {
        "version_type": "new_version",
        "version": result.new_version.version,
        "release_date": (
            result.new_version.release_date
        ),
        "highlights": " | ".join(
            result.new_version.highlights
        ),
        "notes": " | ".join(
            result
            .new_version
            .bugfix_or_regression_topics
        ),
    },
]


csv_path = (
    OUTPUT_DIR
    / "pandas_version_comparison.csv"
)

with csv_path.open(
    "w",
    newline="",
    encoding="utf-8-sig",
) as csv_file:

    fieldnames = [
        "version_type",
        "version",
        "release_date",
        "highlights",
        "notes",
    ]

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(csv_rows)


print_title("Validated Result")
print(
    result.model_dump_json(
        indent=2
    )
)

print()
print("JSON 저장:", json_path)
print("CSV 저장:", csv_path)
