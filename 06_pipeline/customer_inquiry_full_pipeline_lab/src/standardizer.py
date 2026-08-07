from __future__ import annotations

from datetime import datetime

import pandas as pd


DATE_FORMATS = [
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M",
    "%d-%m-%Y %H:%M",
    "%Y.%m.%d %H:%M",
]


def clean_text_series(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def parse_mixed_datetime(value: str):
    text = str(value).strip()
    if not text:
        return pd.NaT
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    return pd.NaT


def standardize_inquiries(
    raw_df: pd.DataFrame,
    references: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    dataframe = raw_df.copy()
    dataframe.insert(0, "source_row_number", range(1, len(dataframe) + 1))

    text_columns = [
        "source_inquiry_id",
        "author_name_raw",
        "country_name_raw",
        "language_code_raw",
        "posted_at_raw",
        "inquiry_type_raw",
        "priority_raw",
        "product_code_raw",
        "product_name_raw",
        "answer_status_raw",
        "inquiry_title_raw",
        "inquiry_text_raw",
        "source_url",
    ]
    for column in text_columns:
        dataframe[column] = clean_text_series(dataframe[column])

    dataframe["source_inquiry_id"] = dataframe["source_inquiry_id"].str.upper()
    dataframe["author_name"] = dataframe["author_name_raw"]
    dataframe["posted_at"] = dataframe["posted_at_raw"].map(parse_mixed_datetime)
    dataframe["inquiry_title"] = dataframe["inquiry_title_raw"]
    dataframe["inquiry_text"] = dataframe["inquiry_text_raw"]
    dataframe["language_code"] = dataframe["language_code_raw"]

    mappings = [
        ("inquiry_type", "inquiry_type_raw", "raw_value"),
        ("priority", "priority_raw", "raw_value"),
        ("answer_status", "answer_status_raw", "raw_value"),
        ("country", "country_name_raw", "raw_country_name"),
    ]
    for reference_name, left_column, right_column in mappings:
        dataframe = (
            dataframe.merge(
                references[reference_name],
                how="left",
                left_on=left_column,
                right_on=right_column,
            ).drop(columns=[right_column])
        )

    dataframe["product_code"] = dataframe["product_code_raw"].str.upper()
    dataframe["product_name"] = dataframe["product_name_raw"]
    product_reference = references["product"].rename(
        columns={"product_name": "reference_product_name"}
    )
    dataframe = dataframe.merge(product_reference, how="left", on="product_code")

    dataframe["priority_level"] = pd.to_numeric(
        dataframe["priority_level"], errors="coerce"
    ).astype("Int64")
    dataframe["collected_at"] = pd.to_datetime(
        dataframe["collected_at"], errors="coerce"
    )
    dataframe["standardized_at"] = pd.Timestamp.now().floor("s")
    return dataframe