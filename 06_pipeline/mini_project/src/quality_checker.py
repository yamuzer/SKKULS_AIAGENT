from __future__ import annotations

from typing import Any

import pandas as pd

from src.models import ValidationResult


def is_blank(value: Any) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def validate_books(
    standardized_df: pd.DataFrame,
    rules: dict[str, Any],
) -> ValidationResult:
    issues: list[dict[str, Any]] = []
    duplicate_key = rules["duplicate_key"]
    duplicate_mask = (
        standardized_df[duplicate_key].duplicated(keep=False)
        & standardized_df[duplicate_key].ne("")
    )

    def add_issue(
        row: pd.Series,
        rule_code: str,
        column_name: str,
        invalid_value: Any,
        message: str,
    ) -> None:
        issues.append(
            {
                "source_row_number": int(row["source_row_number"]),
                "source_inquiry_id": str(row.get("source_inquiry_id", "")),
                "rule_code": rule_code,
                "column_name": column_name,
                "invalid_value": "" if pd.isna(invalid_value) else str(invalid_value),
                "error_message": message,
            }
        )

    for row_index, row in standardized_df.iterrows():
        for required_rule in rules["required_fields"]:
            column = required_rule["column"]
            if is_blank(row.get(column)):
                add_issue(
                    row,
                    required_rule["rule_code"],
                    column,
                    row.get(column),
                    required_rule["message"],
                )

        if bool(duplicate_mask.loc[row_index]):
            add_issue(
                row,
                "DUPLICATE_SOURCE_INQUIRY_ID",
                duplicate_key,
                row.get(duplicate_key),
                "원천 문의번호가 중복되었습니다.",
            )

        product_rule = rules["conditional_product_rule"]
        inquiry_type = row.get("inquiry_type_code")
        if (
            not is_blank(inquiry_type)
            and inquiry_type not in product_rule["exempt_inquiry_type_codes"]
        ):
            for column in product_rule["required_columns"]:
                if is_blank(row.get(column)):
                    add_issue(
                        row,
                        product_rule["rule_code"],
                        column,
                        row.get(column),
                        product_rule["message"],
                    )

        product_code = row.get("product_code")
        product_name = row.get("product_name")
        reference_name = row.get("reference_product_name")
        if not is_blank(product_code):
            if is_blank(reference_name):
                add_issue(
                    row,
                    "UNKNOWN_PRODUCT_CODE",
                    "product_code",
                    product_code,
                    "상품코드가 상품 기준정보에 없습니다.",
                )
            elif not is_blank(product_name) and str(product_name) != str(reference_name):
                rule = rules["product_name_rule"]
                add_issue(
                    row,
                    rule["rule_code"],
                    "product_name",
                    product_name,
                    rule["message"],
                )

        if not is_blank(row.get("country_code")):
            raw_language = str(row.get("language_code_raw", "")).split("-")[0].lower()
            default_language = str(row.get("default_language_code", "")).split("-")[0].lower()
            if raw_language and default_language and raw_language != default_language:
                rule = rules["language_country_rule"]
                add_issue(
                    row,
                    rule["rule_code"],
                    "language_code_raw",
                    row.get("language_code_raw"),
                    rule["message"],
                )

    issue_df = pd.DataFrame(
        issues,
        columns=[
            "source_row_number",
            "source_inquiry_id",
            "rule_code",
            "column_name",
            "invalid_value",
            "error_message",
        ],
    )

    invalid_rows = (
        set(issue_df["source_row_number"].astype(int))
        if not issue_df.empty
        else set()
    )
    row_result_df = standardized_df.copy()
    row_result_df["quality_status"] = row_result_df["source_row_number"].map(
        lambda value: "INVALID" if int(value) in invalid_rows else "VALID"
    )

    issue_counts = (
        issue_df.groupby("source_row_number").size().to_dict()
        if not issue_df.empty
        else {}
    )
    row_result_df["quality_issue_count"] = row_result_df["source_row_number"].map(
        lambda value: int(issue_counts.get(int(value), 0))
    ).astype("Int64")

    valid_df = row_result_df[row_result_df["quality_status"].eq("VALID")].reset_index(drop=True)
    invalid_df = row_result_df[row_result_df["quality_status"].eq("INVALID")].reset_index(drop=True)

    return ValidationResult(
        valid_df=valid_df,
        invalid_df=invalid_df,
        issue_detail_df=issue_df.sort_values(
            ["source_row_number", "rule_code"]
        ).reset_index(drop=True),
        row_result_df=row_result_df.reset_index(drop=True),
    )
