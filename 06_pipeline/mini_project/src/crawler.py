from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
import requests
import re
from bs4 import BeautifulSoup

from src.models import CrawlResult


class QuietRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

def _normalize_text(value: str) -> str:
    return " ".join(str(value).split())


def _get_text(parent, selector: str) -> str:
    element = parent.select_one(selector)
    if element is None:
        return ""
    return _normalize_text(element.get_text(" ", strip=True))


def fetch_html(url: str) -> tuple[str, dict[str, Any]]:
    response = requests.get(
        url,
        headers={
            "User-Agent": "CustomerInquiryFullPipeline/1.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ko-KR,ko;q=0.9",
        },
        timeout=10,
    )
    response.raise_for_status()
    response.encoding = "utf-8"

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        raise ValueError(f"HTML 응답이 아닙니다: {content_type}")

    return response.text, {
        "request_url": url,
        "final_url": response.url,
        "http_status": response.status_code,
        "content_type": content_type,
        "response_encoding": response.encoding,
        "html_character_count": len(response.text),
    }


def parse_raw_inquiries(
    html_text: str,
    source_url: str,
    collected_at: datetime,
) -> pd.DataFrame:
    soup = BeautifulSoup(html_text, "html.parser")
    items = soup.select("div.ss_book_list:nth-child(1) > ul")
    if not items:
        raise RuntimeError(".ss_book_list > ul요소를 찾지 못했습니다.")

    rows = []
    rank_idx = 0
    for item in items:
        rank_idx += 1
        rows.append(
            {
                "rank_raw" : rank_idx,
                "title_raw": _get_text(item, ".bo3"),
                "author_raw": _get_text(item, "li:nth-child(3) >a" ),
                "pulisher_raw": _get_text(item, "li:nth-child(3) > a:nth-child(2)"),
                "publish_date_raw": re.search(r'\d{4}년\s*\d{1,2}월', _get_text(item, "li:nth-child(3)")).group(0),
                "price_raw": _get_text(item, "li:nth-child(4) > span:nth-child(1)"),
                "salePrice_raw": _get_text(item, "li:nth-child(4) > span:nth-child(2) > em"),
                "discountRate_raw": _get_text(item, "li:nth-child(4) > span:nth-child(3)"),
                "mileage_raw": _get_text(item, "li:nth-child(4) > span:nth-child(4)"),
                "satisfaction_raw": _get_text(item, "li:nth-child(5) > span.star_score"),
                "reviewCount_raw": _get_text(item, "li:nth-child(5) > a"),
                "salesPoint_raw": _get_text(item, "li:nth-child(5) > span.star_score")
            }
        )
        # print(rows)
    raw_df = pd.DataFrame(rows)
    # print(raw_df)
    # raw_df["collected_at"] = pd.to_datetime(raw_df["collected_at"])
    return raw_df


def build_collection_summary(
    raw_df: pd.DataFrame,
    metadata: dict[str, Any],
    started_at: datetime,
    completed_at: datetime,
) -> pd.DataFrame:
    rows = [
        ["pipeline_started_at", started_at.isoformat(sep=" ", timespec="seconds"), "수집 시작 시각"],
        ["pipeline_completed_at", completed_at.isoformat(sep=" ", timespec="seconds"), "수집 완료 시각"],
        ["request_url", metadata["request_url"], "요청 URL"],
        ["final_url", metadata["final_url"], "최종 URL"],
        ["http_status", metadata["http_status"], "HTTP 상태코드"],
        ["content_type", metadata["content_type"], "응답 콘텐츠 유형"],
        ["html_character_count", metadata["html_character_count"], "HTML 문자 수"],
        ["collected_row_count", len(raw_df), "추출 아이템 행 수"],
        ["unique_source_id_count", int(raw_df["rank_raw"].nunique(dropna=False)), "고유 문의번호 수"],
    ]
    return pd.DataFrame(rows, columns=["metric_name", "metric_value", "description"])


def crawl_to_files(
    site_dir: Path,
    url: str,
    # host: str,
    # port: int,
    raw_html_path: Path,
    raw_csv_path: Path,
    collection_csv_path: Path,
    collection_json_path: Path,
) -> CrawlResult:
    started_at = datetime.now().replace(microsecond=0)

    # with run_local_server(site_dir=site_dir, host=host, port=port):
    #     html_text, metadata = fetch_html(url)
    #     raw_df = parse_raw_inquiries(
    #         html_text=html_text,
    #         source_url=metadata["final_url"],
    #         collected_at=started_at,
    #     )
    html_text, metadata = fetch_html(url)
    raw_df = parse_raw_inquiries(
        html_text=html_text,
        source_url=metadata["final_url"],
        collected_at=started_at,
    )

    completed_at = datetime.now().replace(microsecond=0)
    summary_df = build_collection_summary(
        raw_df=raw_df,
        metadata=metadata,
        started_at=started_at,
        completed_at=completed_at,
    )

    raw_html_path.parent.mkdir(parents=True, exist_ok=True)
    collection_csv_path.parent.mkdir(parents=True, exist_ok=True)

    raw_html_path.write_text(html_text, encoding="utf-8")
    raw_df.to_csv(
        raw_csv_path,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d %H:%M:%S",
    )
    summary_df.to_csv(collection_csv_path, index=False, encoding="utf-8-sig")
    payload = {
        row["metric_name"]: row["metric_value"]
        for row in summary_df.to_dict(orient="records")
    }
    collection_json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    return CrawlResult(raw_df=raw_df, metadata=metadata)
