from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / "data" / "community_event_board.html"
OUTPUT_DIR = BASE_DIR / "output" / "problem1"
BASE_URL = "https://culture.example.com"


def load_soup() -> BeautifulSoup:
    if not HTML_PATH.exists():
        raise FileNotFoundError(
            f"HTML 파일이 없습니다: {HTML_PATH}"
        )

    html_text = HTML_PATH.read_text(encoding="utf-8")

    return BeautifulSoup(
        html_text,
        "html.parser",
    )


def extract_query_value(
    url: str,
    key: str,
) -> str:
    query_values = parse_qs(
        urlparse(url).query
    )

    return query_values.get(
        key,
        [""],
    )[0]


def extract_integer(text: str) -> int:
    number_text = "".join(
        character
        for character in text
        if character.isdigit()
    )

    return int(number_text) if number_text else 0


def extract_float(text: str) -> float:
    value = text.replace("평점", "").strip()
    return float(value)


def find_event_summary_table(
    soup: BeautifulSoup,
):
    required_headers = {
        "행사번호",
        "행사명",
        "지역",
        "신청상태",
    }

    for table in soup.select("table"):
        header_values = {
            th.get_text(
                " ",
                strip=True,
            )
            for th in table.select("th")
        }

        if required_headers.issubset(
            header_values
        ):
            return table

    return None


def parse_event_cards(
    soup: BeautifulSoup,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    cards = soup.select(
        "#event-board > article.event-card"
    )

    for card in cards:
        event_no = card.get(
            "data-event-no",
            "",
        )

        region = card.get(
            "data-region",
            "",
        )

        capacity = int(
            card.get(
                "data-capacity",
                "0",
            )
        )

        fee = int(
            card.get(
                "data-fee",
                "0",
            )
        )

        detail_link = card.select_one(
            "a.event-detail-link"
        )

        if detail_link is None:
            continue

        relative_url = detail_link.get(
            "href",
            "",
        )

        time_tag = card.select_one(
            "time[datetime]"
        )

        if time_tag is None:
            continue

        row = {
            "event_no": event_no,
            "event_id": extract_query_value(
                relative_url,
                "event_id",
            ),
            "event_name": card.select_one(
                ".event-name"
            ).get_text(
                " ",
                strip=True,
            ),
            "region": region,
            "category": card.select_one(
                ".event-category"
            ).get_text(
                " ",
                strip=True,
            ),
            "organizer": card.select_one(
                ".organizer strong"
            ).get_text(
                " ",
                strip=True,
            ),
            "start_at": time_tag.get(
                "datetime",
                "",
            ),
            "location": card.select_one(
                ".event-location"
            ).get_text(
                " ",
                strip=True,
            ),
            "fee": fee,
            "rating": extract_float(
                card.select_one(
                    ".event-rating"
                ).get_text(
                    " ",
                    strip=True,
                )
            ),
            "applicants": extract_integer(
                card.select_one(
                    ".applicant-count"
                ).get_text(
                    " ",
                    strip=True,
                )
            ),
            "capacity": capacity,
            "registration_status": card.select_one(
                ".registration-status"
            ).get_text(
                " ",
                strip=True,
            ),
            "event_url": urljoin(
                BASE_URL,
                relative_url,
            ),
        }

        rows.append(row)

    dataframe = pd.DataFrame(rows)

    dataframe["start_at"] = pd.to_datetime(
        dataframe["start_at"],
    )

    integer_columns = [
        "fee",
        "applicants",
        "capacity",
    ]

    for column_name in integer_columns:
        dataframe[column_name] = dataframe[
            column_name
        ].astype("int64")

    dataframe["rating"] = dataframe[
        "rating"
    ].astype("float64")

    return dataframe


def parse_summary_table(
    soup: BeautifulSoup,
) -> pd.DataFrame:
    summary_table = find_event_summary_table(
        soup
    )

    if summary_table is None:
        raise RuntimeError(
            "행사 요약 표를 찾지 못했습니다."
        )

    header_names = [
        th.get_text(
            " ",
            strip=True,
        )
        for th in summary_table.select(
            "thead th"
        )
    ]

    rows: list[list[str]] = []

    for row in summary_table.select(
        "tbody > tr"
    ):
        cells = row.select(
            ":scope > td"
        )

        values = [
            cell.get_text(
                " ",
                strip=True,
            )
            for cell in cells
        ]

        if len(values) == len(header_names):
            rows.append(values)

    return pd.DataFrame(
        rows,
        columns=header_names,
    )


def print_selector_counts(
    soup: BeautifulSoup,
) -> None:
    selector_map = {
        "전체 행사 카드":
            "#event-board > article.event-card",

        "추천 행사가 아닌 카드":
            "#event-board > article.event-card:not(.recommended)",

        "신청마감 카드":
            "#event-board > article.event-card"
            ":has(.registration-status.closed)",

        "비추천 신청가능 카드":
            "#event-board > article.event-card"
            ":not(.recommended)"
            ":has(.registration-status.open)",

        "홀수 번째 카드":
            "#event-board > article:nth-of-type(odd)",

        "4n+1 번째 카드":
            "#event-board > article:nth-of-type(4n+1)",

        "온라인 행사 카드":
            "#event-board > article.online-event",
    }

    for label, selector in selector_map.items():
        tags = soup.select(selector)
        print(f"{label}: {len(tags)}개")


def main() -> None:
    soup = load_soup()

    print("=" * 72)
    print("1. 문서 기본 정보")
    print("=" * 72)

    page_title = (
        soup.title.get_text(
            " ",
            strip=True,
        )
        if soup.title
        else ""
    )

    heading = soup.select_one(
        "h1#board-title"
    )

    description = soup.select_one(
        ".board-description"
    )

    print("문서 title:", page_title)
    print(
        "페이지 제목:",
        heading.get_text(" ", strip=True),
    )
    print(
        "페이지 설명:",
        description.get_text(" ", strip=True),
    )
    print("태그 이름:", heading.name)
    print("태그 id:", heading.get("id"))

    print()
    print("=" * 72)
    print("2. 지역 메뉴")
    print("=" * 72)

    for link in soup.select(
        ".region-menu > li > a"
    ):
        print(
            f"지역={link.get_text(' ', strip=True)}, "
            f"href={link.get('href')}, "
            f"지역코드={link.get('data-region-code')}"
        )

    print()
    print("=" * 72)
    print("3. 단일 행사 찾기")
    print("=" * 72)

    target_event = soup.find(
        "article",
        {
            "data-event-no": "EVT-26008",
        },
    )

    if target_event is None:
        raise RuntimeError(
            "EVT-26008 행사를 찾지 못했습니다."
        )

    print(
        "행사명:",
        target_event.select_one(
            ".event-name"
        ).get_text(" ", strip=True),
    )

    print(
        "주최기관:",
        target_event.select_one(
            ".organizer strong"
        ).get_text(" ", strip=True),
    )

    print(
        "평점:",
        target_event.select_one(
            ".event-rating"
        ).get_text(" ", strip=True),
    )

    print(
        "신청상태:",
        target_event.select_one(
            ".registration-status"
        ).get_text(" ", strip=True),
    )

    print()
    print("=" * 72)
    print("4. CSS 선택자 결과")
    print("=" * 72)

    print_selector_counts(soup)

    print()
    print("=" * 72)
    print("5. 전체 행사 카드 추출")
    print("=" * 72)

    event_df = parse_event_cards(soup)
    summary_df = parse_summary_table(soup)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    event_df.to_csv(
        OUTPUT_DIR / "community_events.csv",
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d %H:%M:%S",
    )

    summary_df.to_csv(
        OUTPUT_DIR / "event_summary_table.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(event_df.head(5).to_string(index=False))

    print()
    print("[자료형]")
    print(event_df.dtypes)

    recommended_count = len(
        soup.select(
            "#event-board > article.recommended"
        )
    )

    closed_count = int(
        (
            event_df["registration_status"]
            == "신청마감"
        ).sum()
    )

    free_count = int(
        (event_df["fee"] == 0).sum()
    )

    card_event_ids = set(
        event_df["event_no"].tolist()
    )

    table_event_ids = set(
        summary_df["행사번호"].tolist()
    )

    print()
    print("=" * 72)
    print("6. 결과 검증")
    print("=" * 72)

    print("행사 카드 추출 수:", len(event_df))
    print("요약 표 행 수:", len(summary_df))
    print("추천 행사 수:", recommended_count)
    print("신청마감 행사 수:", closed_count)
    print("무료 행사 수:", free_count)
    print(
        "카드와 표의 행사번호 일치:",
        card_event_ids == table_event_ids,
    )
    print("저장 폴더:", OUTPUT_DIR)


if __name__ == "__main__":
    main()