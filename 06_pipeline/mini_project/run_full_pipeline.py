from __future__ import annotations

import argparse
from pathlib import Path

from src.models import PipelinePaths
from src.pipeline import run_full_pipeline


BASE_DIR = Path(__file__).resolve().parent


PATHS = PipelinePaths(
    site_dir='https://www.aladin.co.kr/shop/common/wbest.aspx?BestType=MonthlyBest&BranchType=1&CID=0&Year=2026&Month=8&Week=1&page=1&cnt=1000&SortOrder=1',
    raw_html=BASE_DIR / "data" / "raw" / "aladin_monthly_best.html",
    raw_csv=BASE_DIR / "data" / "raw" / "aladin_monthly_best_raw.csv",
    collection_csv=BASE_DIR / "reports" / "collection_summary.csv",
    collection_json=BASE_DIR / "reports" / "collection_summary.json",
    reference_dir=BASE_DIR / "config" / "reference",
    quality_rules=BASE_DIR / "config" / "quality_rules.json",
    standardized_csv=(
        BASE_DIR / "output" / "standardized" / "aladin_monthly_best_standardized.csv"
    ),
    quality_result_csv=(
        BASE_DIR / "output" / "quality" / "aladin_monthly_best_quality_result.csv"
    ),
    valid_csv=BASE_DIR / "output" / "quality" / "aladin_monthly_best_valid.csv",
    invalid_csv=BASE_DIR / "output" / "quality" / "aladin_monthly_best_invalid.csv",
    issue_csv=BASE_DIR / "output" / "quality" / "aladin_monthly_best_issue_detail.csv",
    missing_csv=BASE_DIR / "reports" / "missing_value_summary.csv",
    rule_csv=BASE_DIR / "reports" / "quality_rule_summary.csv",
    country_csv=BASE_DIR / "reports" / "quality_by_country.csv",
    inquiry_type_csv=BASE_DIR / "reports" / "quality_by_inquiry_type.csv",
    quality_json=BASE_DIR / "reports" / "quality_report.json",
    quality_html=BASE_DIR / "reports" / "aladin_monthly_best_quality_report.html",
    execution_json=BASE_DIR / "reports" / "pipeline_execution_summary.json",
    database_json=BASE_DIR / "reports" / "database_load_summary.json",
)

ENV_PATH = BASE_DIR / "config" / ".env"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "정적 고객 문의 페이지 크롤링부터 품질 분석과 "
            "선택적 PostgreSQL 적재까지 실행합니다."
        )
    )
    # parser.add_argument(
    #     "--skip-crawl",
    #     default=True,
    #     action="store_true",
    #     help="크롤링을 생략하고 기존 data/raw/aladin_monthly_best_raw.csv를 사용합니다.",
    # )
    parser.add_argument(
        "--load-db",
        action="store_true",
        help="품질 결과 생성 후 PostgreSQL에도 적재합니다.",
    )
    # parser.add_argument(
    #     "--port",
    #     type=int,
    #     default=8030,
    #     help="실습용 로컬 HTTP 서버 포트입니다. 기본값은 8030입니다.",
    # )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    print("=" * 80)
    print("크롤링 포함 고객 문의 전체 품질 파이프라인")
    print("=" * 80)
    print("1. 정적 고객 문의 크롤링")
    print("2. 기준정보 기반 표준화")
    print("3. 품질 규칙 검증")
    print("4. 정상·오류 분리와 리포트 저장")
    print("5. PostgreSQL 적재" if arguments.load_db else "5. PostgreSQL 적재 생략")

    result = run_full_pipeline(
        paths=PATHS,
        # host="127.0.0.1",
        # port=arguments.port,
        skip_crawl=False,
        load_database=arguments.load_db,
        env_path=ENV_PATH,
    )

    # payload = result.report.payload
    # print()
    # print("[파이프라인 결과]")
    # print("크롤링:", "SUCCESS" if result.crawl else "SKIPPED")
    # print("전체:", payload["total_count"])
    # print("정상:", payload["valid_count"])
    # print("오류:", payload["invalid_count"])
    # print("품질 이슈:", payload["quality_issue_count"])
    # print("정상률:", f'{payload["valid_rate"]}%')

    print()
    print("[핵심 결과 파일]")
    print("원본 HTML:", PATHS.raw_html)
    print("원천 CSV:", PATHS.raw_csv)
    print("표준화 CSV:", PATHS.standardized_csv)
    # print("정상 CSV:", PATHS.valid_csv)
    # print("오류 CSV:", PATHS.invalid_csv)
    # print("오류 상세:", PATHS.issue_csv)
    # print("HTML 리포트:", PATHS.quality_html)
    # print("실행 요약:", PATHS.execution_json)

    # if result.database_summary:
    #     print()
    #     print("[PostgreSQL 적재]")
    #     print("execution_id:", result.database_summary["execution_id"])
    #     print("적재 건수:", result.database_summary["loaded_counts"])


if __name__ == "__main__":
    main()
