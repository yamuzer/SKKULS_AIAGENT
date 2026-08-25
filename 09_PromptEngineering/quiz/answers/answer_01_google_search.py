import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
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


prompt = """
2026년 8월 현재 pandas의 최신 안정 버전을
반드시 Google Search Tool로 조사하라.

다음 내용을 포함하라.

1. 최신 안정 버전
2. 공식 릴리스 날짜
3. 주요 변경 또는 수정 사항 3개

중요 규칙:
- 반드시 Google Search를 사용한다.
- 기억에 의존하여 최신 버전을 단정하지 않는다.
- 가능하면 pandas 공식 문서를 가장 우선적인 근거로 사용한다.
- 검색으로 확인되지 않은 사실은 추측하지 않는다.
"""


interaction = client.interactions.create(
    model=MODEL_NAME,
    input=prompt,
    tools=[
        {
            "type": "google_search"
        }
    ],
)


print_title("1. Final Answer")
print(interaction.output_text)


steps = interaction.steps or []

citation_rows = []

print_title("2. Interaction Steps")

for index, step in enumerate(
    steps,
    start=1,
):
    step_type = getattr(
        step,
        "type",
        None,
    )

    print()
    print(f"[{index}] {step_type}")

    # --------------------------------------------------------
    # Google Search Call
    # --------------------------------------------------------

    if step_type == "google_search_call":

        arguments = getattr(
            step,
            "arguments",
            None,
        )

        queries = getattr(
            arguments,
            "queries",
            None,
        )

        print("검색 query:", queries)

    # --------------------------------------------------------
    # Google Search Result
    # --------------------------------------------------------

    elif step_type == "google_search_result":

        result = getattr(
            step,
            "result",
            None,
        )

        print(
            "search result 존재:",
            bool(result),
        )

    # --------------------------------------------------------
    # Model Output + URL Citation
    # --------------------------------------------------------

    elif step_type == "model_output":

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

            text = getattr(
                block,
                "text",
                None,
            )

            print()
            print("----- model output text -----")
            print(text)

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
                print("URL Citation")
                print("title:", title)
                print("url:", url)
                print("start_index:", start_index)
                print("end_index:", end_index)

                citation_rows.append(
                    {
                        "title": title or "",
                        "url": url or "",
                        "start_index": start_index,
                        "end_index": end_index,
                    }
                )


output_path = (
    OUTPUT_DIR
    / "search_citations.csv"
)

with output_path.open(
    "w",
    newline="",
    encoding="utf-8-sig",
) as csv_file:

    fieldnames = [
        "title",
        "url",
        "start_index",
        "end_index",
    ]

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(
        citation_rows
    )


print_title("3. CSV 저장")
print("저장 경로:", output_path)
