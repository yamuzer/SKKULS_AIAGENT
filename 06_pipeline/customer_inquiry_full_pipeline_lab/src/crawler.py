from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.models import CrawlResult


class QuietRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


@contextmanager
def run_local_server(site_dir: Path, host: str, port: int) -> Iterator[None]:
    handler = partial(QuietRequestHandler, directory=str(site_dir))
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield
    finally:
        server.shutdown()
        server.server_close()


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
    cards = soup.select(".inquiry-card")
    if not cards:
        raise RuntimeError(".inquiry-card 요소를 찾지 못했습니다.")

    rows = []
    for card in cards:
        rows.append(
            {
                "source_inquiry_id": _normalize_text(
                    card.get("data-inquiry-id", "")
                ),
                "author_name_raw": _get_text(card, ".author-name"),
                "country_name_raw": _get_text(card, ".country-name"),
                "language_code_raw": _get_text(card, ".language-code"),
                "posted_at_raw": _get_text(card, ".posted-at"),
                "inquiry_type_raw": _get_text(card, ".inquiry-type"),
                "priority_raw": _get_text(card, ".priority"),
                "product_code_raw": _get_text(card, ".product-code"),
                "product_name_raw": _get_text(card, ".product-name"),
                "answer_status_raw": _get_text(card, ".answer-status"),
                "inquiry_title_raw": _get_text(card, ".inquiry-title"),
                "inquiry_text_raw": _get_text(card, ".inquiry-text"),
                "source_url": source_url,
                "collected_at": collected_at,
            }
        )

    raw_df = pd.DataFrame(rows)
    raw_df["collected_at"] = pd.to_datetime(raw_df["collected_at"])
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
        ["collected_row_count", len(raw_df), "추출 문의 행 수"],
        ["unique_source_id_count", int(raw_df["source_inquiry_id"].nunique(dropna=False)), "고유 문의번호 수"],
    ]
    return pd.DataFrame(rows, columns=["metric_name", "metric_value", "description"])


def crawl_to_files(
    site_dir: Path,
    url: str,
    host: str,
    port: int,
    raw_html_path: Path,
    raw_csv_path: Path,
    collection_csv_path: Path,
    collection_json_path: Path,
) -> CrawlResult:
    started_at = datetime.now().replace(microsecond=0)

    with run_local_server(site_dir=site_dir, host=host, port=port):
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
