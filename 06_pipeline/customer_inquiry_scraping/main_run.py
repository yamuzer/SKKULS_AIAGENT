from datetime import datetime
from pathlib import Path

from src.static_crawler import (
    run_local_server,
    fetch_html,
    parse_raw_inquiries,
    create_collection_summary,
    save_outputs
)

BASE_DIR = Path(__file__).resolve().parent

SITE_DIR = BASE_DIR / "site"
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "output"

HOST = "127.0.0.1"
PORT = 8015

TARGET_URL = f'http://{HOST}:{PORT}/customer_inquiries.html'

RAW_HTML_PATH = RAW_DIR / "customer_inquiry_page.html"
RAW_CSV_PATH = RAW_DIR / "customer_inquiry_raw.csv"

SUMMARY_CSV_PATH = REPORT_DIR / "collection_summary.csv"
SUMMARY_JSON_PATH = REPORT_DIR / "collection_summary.json"

def print_title(title: str) -> None:
    print()
    print('=' * 100)
    print(title)
    print('=' * 100)

def main() -> None:
    started_at = datetime.now().replace(microsecond=0)
    #print(started_at)
    print_title('서버 구동')

    with run_local_server(
        site_dir=SITE_DIR,
        host=HOST,
        port=PORT,
    ):
        print_title('페이지 요청')
        html_text, metadata = fetch_html(TARGET_URL)
        print(f'HTTP 상태: {metadata["http_status"]}')

        print_title('고객 문의 원천값 추출')
        raw_df = parse_raw_inquiries(
            html_text=html_text,
            source_url=metadata['final_url'],
            collected_at=started_at,
        )

        print(f'추출 행: {len(raw_df)}')

        completed_at = datetime.now().replace(microsecond=0)

        print_title('수집 요약 생성')

        summary = create_collection_summary(
            raw_df=raw_df,
            metadata=metadata,
            started_at=started_at,
            completed_at=completed_at
        )

        '''
        print()
        summary.info()
        print(summary.iloc[0]['description'])
        '''

        print_title('원천 파일 저장')
        save_outputs(
            html_text=html_text,
            raw_df=raw_df,
            summary_df=summary,
            raw_html_path=RAW_HTML_PATH,
            raw_csv_path=RAW_CSV_PATH,
            summary_csv_path=SUMMARY_CSV_PATH,
            summary_json_path=SUMMARY_JSON_PATH
        )

if "__main__" == __name__:
    main()