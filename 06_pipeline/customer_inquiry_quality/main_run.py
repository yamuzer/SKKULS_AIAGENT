from pathlib import Path

from src.data_loader import (
     load_raw_data,
     load_reference_data,
     load_quality_rules
)

from src.standardizer import standardize_inquiries
from src.quality_checker import validate_inquiries

from src.report_builder import (
    create_missing_value_summary,
    create_quality_by_group,
    create_rule_summary,
    create_report_payload,
    save_report_json,
    save_report_html
)

BASE_DIR = Path(__file__).resolve().parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "customer_inquiry_raw.csv"

REFERENCE_DIR = BASE_DIR / "config" / "reference"

QUALITY_RULES_DIR = BASE_DIR / "config" / "quality_rules.json"

STANDARDIZED_PATH = BASE_DIR / "data" / "standardized" / "customer_inquiry_standardized.csv"

VALID_PATH = BASE_DIR / "data" / "quality" / "customer_inquiry_valid.csv"

INVALID_PATH = BASE_DIR / "data" / "quality" / "customer_inquiry_invalid.csv"

ISSUE_DETAIL_DIR = BASE_DIR / "data" / "quality" / "quality_issue_detail.csv"

ROW_RESULT_PATH = BASE_DIR / "data" / "quality" / "customer_inquiry_quality_result.csv"

MISSING_SUMMARY_PATH = BASE_DIR / "output" / "missing_value_summary.csv"

RULE_SUMMARY_PATH = BASE_DIR / "output" / "quality_rule_summary.csv"

COUNTRY_SUMMARY_PATH = BASE_DIR / "output" / "quality_by_country.csv"

INQUIRY_TYPE_SUMMARY_PATH = BASE_DIR / "output" / "quality_by_inquiry_type.csv"

REPORT_JSON_PATH = BASE_DIR / "output" / "quality_report.json"

REPORT_HTML_PATH = BASE_DIR / "output" / "customer_inquiry_quality_report.html"


def print_title(title: str) -> None:
    print()
    print('=' * 100)
    print(title)
    print('=' * 100)

def main() -> None:
    print_title("1. 원천 데이터와 설정 불러오기")

    raw_df = load_raw_data(RAW_DATA_DIR)

    references = load_reference_data(REFERENCE_DIR)

    rules = load_quality_rules(QUALITY_RULES_DIR)

    print_title('2. 고객 문의 데이터 표준화')

    standardized_df = standardize_inquiries(
        raw_df=raw_df,
        references=references,
    )

    print_title('3. 품질 규칙 적용')

    validation_result = validate_inquiries(
        standardized_df=standardized_df,
        rules=rules,
    )

    print_title('4. 품질 분석 리포트 생성')

    missing_summary_df = create_missing_value_summary(
        standardized_df,
    )

    country_summary_df = create_quality_by_group(
        row_result_df=validation_result.row_result_df,
        group_column="country_code",
        output_group_name='country_code'
    )

    inquiry_type_summary_df = create_quality_by_group(
        row_result_df=validation_result.row_result_df,
        group_column="inquiry_type_code",
        output_group_name='inquiry_type_code'
    )

    rule_summary_df = create_rule_summary(validation_result.issue_detail_df)
    rule_summary_df.info()

    report_payload = create_report_payload(
        standardized_df=standardized_df,
        validation_result=validation_result,
        missing_summary_df=missing_summary_df,
        rule_summary_df=rule_summary_df
    )

    #print(report_payload)

    print_title('CSV, JSON , HTML 결과 저장')

    STANDARDIZED_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALID_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    validation_result.valid_df.to_csv(
        VALID_PATH,
        index=False,
        encoding='utf-8-sig',
        date_format='%Y-%m-%d %H:%M:%S',
    )

    validation_result.invalid_df.to_csv(
        INVALID_PATH,
        index=False,
        encoding='utf-8-sig',
        date_format='%Y-%m-%d %H:%M:%S',
    )

    validation_result.issue_detail_df.to_csv(
        ISSUE_DETAIL_DIR,
        index=False,
        encoding='utf-8-sig',
    )

    validation_result.row_result_df.to_csv(
        ROW_RESULT_PATH,
        index=False,
        encoding='utf-8-sig',
        date_format='%Y-%m-%d %H:%M:%S',
    )

    missing_summary_df.to_csv(
        MISSING_SUMMARY_PATH,
        index=False,
        encoding='utf-8-sig'
    )

    rule_summary_df.to_csv(
        RULE_SUMMARY_PATH,
        index=False,
        encoding='utf-8-sig',
    )

    country_summary_df.to_csv(
        COUNTRY_SUMMARY_PATH,
        index=False,
        encoding='utf-8-sig',
    )

    inquiry_type_summary_df.to_csv(
        INQUIRY_TYPE_SUMMARY_PATH,
        index=False,
        encoding='utf-8-sig',
    )

    save_report_json(
        payload=report_payload,
        output_path=REPORT_JSON_PATH,
    )

    save_report_html(
        payload=report_payload,
        missing_summary_df=missing_summary_df,
        rule_summary_df=rule_summary_df,
        country_summary_df=country_summary_df,
        inquiry_type_summary_df=inquiry_type_summary_df,
        issue_detail_df=validation_result.issue_detail_df,
        output_path=REPORT_HTML_PATH,
    )




if __name__ == "__main__":
    main()














