import json
from pathlib import Path
import pandas as pd
from typing import Any

from src.quality_checker import ValidationResult

def create_missing_value_summary(standardized_df: pd.DataFrame) -> pd.DataFrame:
    #표준화 결과의 열별 결측 건수와 결측률을 계산함

    rows = []
    total_count = len(standardized_df.index)

    target_columns = [
        'author_name',
        'country_code',
        'language_code',
        'posted_at',
        'inquiry_type_code',
        'priority_code',
        'product_code',
        'product_name',
        'answer_status_code',
        'inquiry_title',
        'inquiry_text'
    ]

    for column in target_columns:
        series = standardized_df[column]
        missing_mask = (
            series.isna()
            |
            series.astype("string").fillna("").str.strip().eq('')
        )

        missing_count = int(missing_mask.sum())

        rows.append(
            {
                'column_name': column,
                'total_count': total_count,
                'missing_count': missing_count,
                'missing_rate':round(
                    (missing_count /total_count * 100)
                    if total_count else 0.0,
                    2
                )
            }
        )

    return pd.DataFrame(rows)


def create_quality_by_group(
    row_result_df: pd.DataFrame,
    group_column: str,
    output_group_name: str
) ->pd.DataFrame:
    #국가문의 유형 등 그룹별 품질 결과를 계산

    working_df = row_result_df.copy()

    working_df[group_column] = (
        working_df[group_column]
        .astype("string")
        .fillna("")
        .replace({"":'UNKNOWN'})
    )

    summary_df = (
        working_df
        .groupby(group_column, as_index=False, dropna=False)
        .agg(
            total_count=("source_inquiry_id", "count"),
            valid_count=("quality_status", lambda series: int(series.eq('VALID').sum())),
            invalid_count=("quality_status", lambda series: int(series.eq('INVALID').sum())),
            issue_count=('quality_issue_count', 'sum')
        )
    )

    summary_df['invalid_rate'] = (summary_df['invalid_count'] / summary_df['total_count'] * 100).round(2)

    return summary_df.rename(columns={group_column: output_group_name})



def create_rule_summary(
        issue_detail_df: pd.DataFrame,
)->pd.DataFrame:

    if issue_detail_df.empty:
        return pd.DataFrame(
            columns=[
                'rule_code',
                'issue_count',
                'affected_row_count'
            ]
        )

    return (
        issue_detail_df
        .groupby('rule_code', as_index=False)
        .agg(
            issue_count=("rule_code", "size"),
            affected_row_count=("source_row_index", "nunique")
        )
        .sort_values(['issue_count', 'rule_code'], ascending=[False, True])
        .reset_index(drop=True)
    )



def create_report_payload(
    standardized_df: pd.DataFrame,
    validation_result: ValidationResult,
    missing_summary_df: pd.DataFrame,
    rule_summary_df: pd.DataFrame,
) -> dict[str, Any]:
    #JSON과 HTML 리포터에 사용할 지표를 만듬

    total_count = len(standardized_df)

    valid_count = len(validation_result.valid_df)
    invalid_count = len(validation_result.invalid_df)
    issue_count = len(validation_result.issue_detail_df)

    return {
        'total_count': total_count,
        'valid_count': valid_count,
        'invalid_count': invalid_count,
        'valid_rate': round(
            (valid_count / total_count * 100)
            if total_count else 0.0,
            2
        ),
        'invalid_rate': round(
            (invalid_count / total_count * 100)
            if total_count else 0.0,
            2
        ),
        'quality_issue_count': issue_count,
        'duplicate_source_id_row_count':int(
            (
                validation_result['issue_detail_df']
                if isinstance(validation_result, dict)
                else validation_result.issue_detail_df
            )['rule_code'].eq('DUPLICATE_SOURCE_INQUIRY_ID').sum()
        )
        if issue_count else 0,
        'missing_summary':missing_summary_df.to_dict(orient='records'),
        'rule_summary':rule_summary_df.to_dict(orient='records'),
    }


def dataframe_to_html_table(
        dataframe: pd.DataFrame,
) -> str:
    if dataframe.empty:
        return (
            "<p class='empty'>"
            "해당 데이터가 없습니다."
            "</p>"
        )

    return dataframe.to_html(
        index=False,
        border=0,
        classes='report-table',
        escape=True
    )


def save_report_json(
    payload: dict[str, Any],
    output_path: Path
) -> None:

    output_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=str
        ),
        encoding='utf-8'
    )


def save_report_html(
    payload: dict[str, Any],
    missing_summary_df: pd.DataFrame,
    rule_summary_df: pd.DataFrame,
    country_summary_df: pd.DataFrame,
    inquiry_type_summary_df: pd.DataFrame,
    issue_detail_df: pd.DataFrame,
    output_path: Path,
) -> None:
    #품질 분석 HTML 보고서 작성

    top_issue_df = issue_detail_df.head(20)

    report_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>고객 문의 데이터 품질 리포트</title>
<style>
body {{
    margin: 0;
    padding: 36px;
    background: #f4f6f8;
    color: #1f2937;
    font-family: Arial, "Malgun Gothic", sans-serif;
}}
.container {{
    max-width: 1200px;
    margin: 0 auto;
}}
.card-grid {{
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 14px;
    margin: 24px 0;
}}
.card {{
    padding: 18px;
    border: 1px solid #dbe1e8;
    border-radius: 12px;
    background: white;
}}
.card strong {{
    display: block;
    margin-top: 8px;
    font-size: 24px;
}}
section {{
    margin-top: 24px;
    padding: 22px;
    border: 1px solid #dbe1e8;
    border-radius: 12px;
    background: white;
}}
.report-table {{
    width: 100%;
    border-collapse: collapse;
}}
.report-table th,
.report-table td {{
    padding: 9px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
}}
.report-table th {{
    background: #f8fafc;
}}
.empty {{
    color: #6b7280;
}}
</style>
</head>
<body>
<div class="container">
    <h1>고객 문의 데이터 품질 리포트</h1>
    <p>원천 CSV를 표준화하고 품질 규칙을 적용한 결과입니다.</p>
    
    <div class="card-grid">
        <div class="card">전체 행<strong>{payload["total_count"]}</strong></div>
        <div class="card">정상 행<strong>{payload["valid_count"]}</strong></div>
        <div class="card">오류 행<strong>{payload["invalid_count"]}</strong></div>
        <div class="card">정상률<strong>{payload["valid_rate"]}</strong></div>
        <div class="card">품질 이슈<strong>{payload["quality_issue_count"]}</strong></div>
    </div>
    
    <section>
        <h2>품질 규칙별 이슈</h2>
        {dataframe_to_html_table(rule_summary_df)}
    </section>
    
    <section>
        <h2>열별 결측 패턴</h2>
        {dataframe_to_html_table(missing_summary_df)}
    </section>
    
    <section>
        <h2>국가별 품질</h2>
        {dataframe_to_html_table(country_summary_df)}
    </section>
    
    <section>
        <h2>문의 유형별 품질</h2>
        {dataframe_to_html_table(inquiry_type_summary_df)}
    </section>
    
    <section>
        <h2>오류 상세 상위 20건</h2>
        {dataframe_to_html_table(top_issue_df)}
    </section>
</div>
</body>
</html>
"""

    output_path.write_text(
        report_html,
        encoding="utf-8"
    )







