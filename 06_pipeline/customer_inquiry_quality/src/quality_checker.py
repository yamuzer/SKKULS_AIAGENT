from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import pandas as pd
from pandas.core.algorithms import duplicated
from pandas.io.sas.sas_constants import row_length_offset_multiplier


@dataclass
class ValidationResult:
    valid_df: pd.DataFrame
    invalid_df: pd.DataFrame
    issue_detail_df: pd.DataFrame
    row_result_df: pd.DataFrame


def is_blank(value: Any) -> bool:
    if pd.isna(value):
        return True

    return str(value).strip() == ""


def add_issue(
    issues: list[dict[str, Any]],
    row_index: int,
    source_inquiry_id: str,
    rule_code: str,
    column_name: str,
    invalid_value: Any,
    error_message: str,
) -> None:
    # 품질 이슈 한 건을 목록에 추가함

    issues.append(
        {
            'source_row_index': row_index,
            'source_inquiry_id': source_inquiry_id,
            'rule_code': rule_code,
            'column_name': column_name,
            'invalid_value': (
                "" if pd.isna(invalid_value) else str(invalid_value)
            ),
            'error_message': error_message,
        }
    )


def validate_inquiries(
    standardized_df: pd.DataFrame,
    rules: dict[str, Any],
) -> ValidationResult:
    '''
    표준화된 고객 문의 데이터에 품질 규칙을 적용
    '''

    issues = []

    duplicate_key = rules['duplicate_key']

    duplicate_mask = (
        standardized_df[duplicate_key].duplicated(keep=False)
        &
        standardized_df[duplicate_key].ne("")
    )

    for row_index, row in standardized_df.iterrows():
        source_id = str(row.get('source_inquiry_id', ""))

        for required_rule in rules['required_fields']:
            column = required_rule['column']

            if is_blank(row.get(column)):
                add_issue(
                    issues=issues,
                    row_index=row_index,
                    source_inquiry_id=source_id,
                    rule_code=required_rule['rule_code'],
                    column_name=column,
                    invalid_value=row.get(column),
                    error_message=required_rule['message'],
                )

        if bool(duplicate_mask.loc[row_index]):
            add_issue(
                issues=issues,
                row_index=row_index,
                source_inquiry_id=source_id,
                rule_code='DUPLICATE_SOURCE_INQUIRY_ID',
                column_name=duplicate_key,
                invalid_value=row.get(duplicate_key),
                error_message='원천 문의번호가 중복되었습니다.',
            )

        product_rule = rules['conditional_product_rule']

        inquiry_type_code = row.get('inquiry_type_code')

        if (not is_blank(inquiry_type_code)
            and inquiry_type_code
            not in product_rule['exempt_inquiry_type_codes']
        ):
            for column in product_rule['required_columns']:
                if is_blank(row.get(column)):
                    add_issue(
                        issues=issues,
                        row_index=row_index,
                        source_inquiry_id=source_id,
                        rule_code=required_rule['rule_code'],
                        column_name=column,
                        invalid_value=row.get(column),
                        error_message=required_rule['message'],
                    )

        product_code = row.get('product_code')
        product_name = row.get('product_name')
        reference_product_name = row.get('reference_product_name')

        if not is_blank(product_code):
            if is_blank(reference_product_name):
                add_issue(
                    issues=issues,
                    row_index=row_index,
                    source_inquiry_id=source_id,
                    rule_code="UNKNOWN_PRODUCT_CODE",
                    column_name='product_code',
                    invalid_value=product_code,
                    error_message='상품코드가 상품 기준정보에 없습니다.',
                )
            elif (not is_blank(product_name)
                  and str(product_name) != str(reference_product_name)
            ):
                name_rule = rules['product_name_rule']
                add_issue(
                    issues=issues,
                    row_index=row_index,
                    source_inquiry_id=source_id,
                    rule_code=required_rule['rule_code'],
                    column_name='product_name',
                    invalid_value=product_name,
                    error_message=name_rule['message'],
                )

        country_code = row.get('country_code')

        if not is_blank(country_code):
            raw_language = str(row.get('language_code_raw', "")).strip()

            default_language = str(row.get('default_language_code', "")).strip()

            normalized_raw_language = raw_language.split("-")[0].lower()
            normalized_default_language = default_language.split("-")[0].lower()

            if (
                normalized_raw_language
                and normalized_default_language
                and normalized_raw_language != normalized_default_language
            ):
                language_rule = rules['languge_country_rule']

                add_issue(
                    issues=issues,
                    row_index=row_index,
                    source_inquiry_id=source_id,
                    rule_code=required_rule['rule_code'],
                    column_name='language_code_raw',
                    invalid_value=raw_language,
                    error_message=language_rule['message'],
                )

    issue_detail_df = pd.DataFrame(
        issues,
        columns=[
            'source_row_index',
            'source_inquiry_id',
            'rule_code',
            'column_name',
            'invalid_value',
            'error_message',
        ]
    )

    if issue_detail_df.empty:
        invalid_indexes = set()
    else:
        invalid_indexes = set(
            issue_detail_df['source_row_index'].astype(int)
        )

    row_result_df = standardized_df.copy()

    row_result_df['quality_status'] = [
        "INVALID" if index in invalid_indexes else 'VALID'
        for index in row_result_df.index
    ]

    issue_count_by_row = (
        issue_detail_df
        .groupby('source_row_index')
        .size()
        .to_dict()
        if not issue_detail_df.empty else {}
    )

    row_result_df['quality_issue_count'] = [
        int(issue_count_by_row.get(index, 0))
        for index in row_result_df.index
    ]

    valid_df = (
        row_result_df[row_result_df['quality_status'].eq('VALID')]
        .reset_index(drop=True)
    )

    invalid_df = (
        row_result_df[row_result_df['quality_status'].eq('INVALID')]
        .reset_index(drop=True)
    )

    return ValidationResult(
        valid_df=valid_df,
        invalid_df=invalid_df,
        issue_detail_df=(
            issue_detail_df
            .sort_values(['source_row_index', 'rule_code'])
            .reset_index(drop=True)
        ),
        row_result_df=row_result_df.reset_index(drop=True),
    )

























