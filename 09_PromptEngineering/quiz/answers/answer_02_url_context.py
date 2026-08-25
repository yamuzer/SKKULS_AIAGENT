import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


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
# official_urls.csv에서 pandas_3_0_0 URL 찾기
# ============================================================

target_url = None

with URL_FILE_PATH.open(
    "r",
    newline="",
    encoding="utf-8-sig",
) as csv_file:

    reader = csv.DictReader(csv_file)

    for row in reader:

        if row["name"] == "pandas_3_0_0":
            target_url = row["url"]
            break


if not target_url:
    raise ValueError(
        "official_urls.csv에서 pandas_3_0_0 URL을 찾지 못했습니다."
    )


print_title("1. Target URL")
print(target_url)


prompt = f"""
다음 pandas 공식 릴리스 노트를
URL Context Tool로 직접 읽어라.

URL:
{target_url}

이 URL에 적힌 내용만 근거로 다음 항목을 한국어로 정리하라.

1. 문서 제목
2. 공식 릴리스 날짜
3. 주요 변화 5개
4. string dtype 관련 변화
5. Copy-on-Write 관련 변화
6. 업그레이드 시 주의할 내용 3개

중요 규칙:
- Google Search를 사용하지 않는다.
- 반드시 제공한 URL의 내용만 사용한다.
- 다른 버전 문서의 사실을 섞지 않는다.
- 페이지에서 확인할 수 없는 사실은 추측하지 않는다.
"""


interaction = client.interactions.create(
    model=MODEL_NAME,
    input=prompt,
    tools=[
        {
            "type": "url_context"
        }
    ],
)


print_title("2. Final Answer")
print(interaction.output_text)


steps = interaction.steps or []

audit_rows = []


# ============================================================
# URL Context Call
# ============================================================

print_title("3. URL Context Call")

for step in steps:

    if getattr(
        step,
        "type",
        None,
    ) != "url_context_call":
        continue

    arguments = getattr(
        step,
        "arguments",
        None,
    )

    urls = getattr(
        arguments,
        "urls",
        None,
    ) or []

    for url in urls:
        print("요청 URL:", url)


# ============================================================
# URL Context Result
# ============================================================

print_title("4. URL Context Result")

for step in steps:

    if getattr(
        step,
        "type",
        None,
    ) != "url_context_result":
        continue

    result_items = getattr(
        step,
        "result",
        None,
    ) or []

    for item in result_items:

        status = getattr(
            item,
            "status",
            None,
        )

        url = getattr(
            item,
            "url",
            None,
        )

        title = getattr(
            item,
            "title",
            None,
        )

        snippet = getattr(
            item,
            "snippet",
            None,
        )

        print()
        print("status:", status)
        print("url:", url)
        print("title:", title)
        print("snippet:", snippet)

        audit_rows.append(
            {
                "record_type": "retrieval",
                "status": status or "",
                "url": url or "",
                "title": title or "",
                "start_index": "",
                "end_index": "",
                "snippet": snippet or "",
            }
        )


# ============================================================
# Model Output Citation
# ============================================================

print_title("5. Model Output URL Citation")

for step in steps:

    if getattr(
        step,
        "type",
        None,
    ) != "model_output":
        continue

    content_blocks = getattr(
        step,
        "content",
        None,
    ) or []

    for block in content_blocks:

        if getattr(
            block,
            "type",
            None,
        ) != "text":
            continue

        annotations = getattr(
            block,
            "annotations",
            None,
        ) or []

        for annotation in annotations:

            if getattr(
                annotation,
                "type",
                None,
            ) != "url_citation":
                continue

            title = getattr(
                annotation,
                "title",
                None,
            )

            url = getattr(
                annotation,
                "url",
                None,
            )

            start_index = getattr(
                annotation,
                "start_index",
                None,
            )

            end_index = getattr(
                annotation,
                "end_index",
                None,
            )

            print()
            print("title:", title)
            print("url:", url)
            print("start_index:", start_index)
            print("end_index:", end_index)

            audit_rows.append(
                {
                    "record_type": "citation",
                    "status": "",
                    "url": url or "",
                    "title": title or "",
                    "start_index": start_index,
                    "end_index": end_index,
                    "snippet": "",
                }
            )


output_path = (
    OUTPUT_DIR
    / "url_context_audit.csv"
)

with output_path.open(
    "w",
    newline="",
    encoding="utf-8-sig",
) as csv_file:

    fieldnames = [
        "record_type",
        "status",
        "url",
        "title",
        "start_index",
        "end_index",
        "snippet",
    ]

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(
        audit_rows
    )


print_title("6. CSV 저장")
print("저장 경로:", output_path)
