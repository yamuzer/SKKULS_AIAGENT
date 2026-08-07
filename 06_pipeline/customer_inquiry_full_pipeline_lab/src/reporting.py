from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.models import ReportResult, ValidationResult


def _missing_mask(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype("string").fillna("").str.strip().eq("")


def create_missing_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "author_name",
        "country_code",
        "language_code",
        "posted_at",
        "inquiry_type_code",
        "priority_code",
        "product_code",
        "product_name",
        "answer_status_code",
        "inquiry_title",
        "inquiry_text",
    ]
    total = len(dataframe)
    rows = []
    for column in columns:
        missing = int(_missing_mask(dataframe[column]).sum())
        rows.append(
            {
                "column_name": column,
                "total_count": total,
                "missing_count": missing,
                "missing_rate": round(missing / total * 100, 2) if total else 0.0,
            }
        )
    return pd.DataFrame(rows)


def create_rule_summary(issue_df: pd.DataFrame) -> pd.DataFrame:
    if issue_df.empty:
        return pd.DataFrame(
            columns=["rule_code", "issue_count", "affected_row_count"]
        )
    return (
        issue_df.groupby("rule_code", as_index=False)
        .agg(
            issue_count=("rule_code", "size"),
            affected_row_count=("source_row_number", "nunique"),
        )
        .sort_values(["issue_count", "rule_code"], ascending=[False, True])
        .reset_index(drop=True)
    )


def create_group_summary(
    row_result_df: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    working = row_result_df.copy()
    working[group_column] = (
        working[group_column]
        .astype("string")
        .fillna("")
        .replace({"": "UNKNOWN"})
    )
    result = (
        working.groupby(group_column, as_index=False, dropna=False)
        .agg(
            total_count=("source_inquiry_id", "count"),
            valid_count=("quality_status", lambda series: int(series.eq("VALID").sum())),
            invalid_count=("quality_status", lambda series: int(series.eq("INVALID").sum())),
            issue_count=("quality_issue_count", "sum"),
        )
    )
    result["invalid_rate"] = (
        result["invalid_count"] / result["total_count"] * 100
    ).round(2)
    return result


def build_report(
    standardized_df: pd.DataFrame,
    validation: ValidationResult,
) -> ReportResult:
    missing_summary = create_missing_summary(standardized_df)
    rule_summary = create_rule_summary(validation.issue_detail_df)
    country_summary = create_group_summary(validation.row_result_df, "country_code")
    inquiry_type_summary = create_group_summary(
        validation.row_result_df,
        "inquiry_type_code",
    )

    total = len(standardized_df)
    valid = len(validation.valid_df)
    invalid = len(validation.invalid_df)
    payload = {
        "total_count": total,
        "valid_count": valid,
        "invalid_count": invalid,
        "quality_issue_count": len(validation.issue_detail_df),
        "valid_rate": round(valid / total * 100, 2) if total else 0.0,
        "invalid_rate": round(invalid / total * 100, 2) if total else 0.0,
    }

    return ReportResult(
        missing_summary=missing_summary,
        rule_summary=rule_summary,
        country_summary=country_summary,
        inquiry_type_summary=inquiry_type_summary,
        payload=payload,
    )


def _html_table(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return "<p>데이터가 없습니다.</p>"
    return dataframe.to_html(
        index=False,
        border=0,
        classes="report-table",
        escape=True,
    )


def save_html_report(
    report: ReportResult,
    validation: ValidationResult,
    path: Path,
) -> None:
    payload = report.payload
    document = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>고객 문의 전체 품질 파이프라인 리포트</title>
<style>
body {{ margin:0; padding:36px; background:#f4f6f8; color:#1f2937; font-family:Arial,'Malgun Gothic',sans-serif; }}
.container {{ max-width:1200px; margin:0 auto; }}
.cards {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:14px; margin:24px 0; }}
.card, section {{ padding:20px; border:1px solid #dbe1e8; border-radius:12px; background:white; }}
.card strong {{ display:block; margin-top:8px; font-size:25px; }}
section {{ margin-top:22px; }}
.report-table {{ width:100%; border-collapse:collapse; }}
.report-table th, .report-table td {{ padding:9px; border-bottom:1px solid #e5e7eb; text-align:left; }}
.report-table th {{ background:#f8fafc; }}
</style>
</head>
<body>
<div class="container">
<h1>크롤링 기반 고객 문의 데이터 품질 파이프라인</h1>
<p>정적 웹페이지 수집부터 품질 분석까지 한 번에 실행한 결과입니다.</p>
<div class="cards">
<div class="card">전체<strong>{payload['total_count']}</strong></div>
<div class="card">정상<strong>{payload['valid_count']}</strong></div>
<div class="card">오류<strong>{payload['invalid_count']}</strong></div>
<div class="card">정상률<strong>{payload['valid_rate']}%</strong></div>
<div class="card">품질 이슈<strong>{payload['quality_issue_count']}</strong></div>
</div>
<section><h2>규칙별 이슈</h2>{_html_table(report.rule_summary)}</section>
<section><h2>결측 패턴</h2>{_html_table(report.missing_summary)}</section>
<section><h2>국가별 품질</h2>{_html_table(report.country_summary)}</section>
<section><h2>문의유형별 품질</h2>{_html_table(report.inquiry_type_summary)}</section>
<section><h2>오류 상세</h2>{_html_table(validation.issue_detail_df.head(20))}</section>
</div>
</body>
</html>"""
    path.write_text(document, encoding="utf-8")


def save_file_outputs(
    standardized_df: pd.DataFrame,
    validation: ValidationResult,
    report: ReportResult,
    paths,
) -> None:
    for path in [
        paths.standardized_csv,
        paths.quality_result_csv,
        paths.valid_csv,
        paths.invalid_csv,
        paths.issue_csv,
        paths.missing_csv,
        paths.rule_csv,
        paths.country_csv,
        paths.inquiry_type_csv,
        paths.quality_json,
        paths.quality_html,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    csv_options = {
        "index": False,
        "encoding": "utf-8-sig",
        "date_format": "%Y-%m-%d %H:%M:%S",
    }
    standardized_df.to_csv(paths.standardized_csv, **csv_options)
    validation.row_result_df.to_csv(paths.quality_result_csv, **csv_options)
    validation.valid_df.to_csv(paths.valid_csv, **csv_options)
    validation.invalid_df.to_csv(paths.invalid_csv, **csv_options)
    validation.issue_detail_df.to_csv(
        paths.issue_csv,
        index=False,
        encoding="utf-8-sig",
    )
    report.missing_summary.to_csv(paths.missing_csv, index=False, encoding="utf-8-sig")
    report.rule_summary.to_csv(paths.rule_csv, index=False, encoding="utf-8-sig")
    report.country_summary.to_csv(paths.country_csv, index=False, encoding="utf-8-sig")
    report.inquiry_type_summary.to_csv(
        paths.inquiry_type_csv,
        index=False,
        encoding="utf-8-sig",
    )
    paths.quality_json.write_text(
        json.dumps(report.payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    save_html_report(report, validation, paths.quality_html)
