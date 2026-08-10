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


def standardize_books(
    raw_df: pd.DataFrame,
    references: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    dataframe = raw_df.copy()
    dataframe.insert(0, "source_row_number", range(1, len(dataframe) + 1))

    text_columns = [
        "rank_raw",
        "title_raw",
        "author_raw",
        "pulisher_raw",
        "publish_date_raw",
        "price_raw",
        "salePrice_raw",
        "discountRate_raw",
        "mileage_raw",
        "satisfaction_raw",
        "reviewCount_raw",
        "salesPoint_raw",
        
    ]
    for column in text_columns:
        dataframe[column] = clean_text_series(dataframe[column])
    dataframe["title"] = dataframe["title_raw"]
    dataframe["author"] = dataframe["author_raw"]
    dataframe["pulisher"] = dataframe["pulisher_raw"]
    dataframe["publish_date"] = pd.to_datetime(dataframe["publish_date_raw"], format='%Y년 %m월')
    dataframe["price"] = pd.to_numeric(dataframe["price_raw"].str.replace(',', ''), errors='coerce')
    dataframe["salePrice"] = pd.to_numeric(dataframe["salePrice_raw"].str.replace(',', '').replace('원', '', regex=False), errors='coerce')
    dataframe["discountRate"] =pd.to_numeric( dataframe["discountRate_raw"].str.replace('%', ''), errors='coerce') / 100
    dataframe["mileage"] = pd.to_numeric(dataframe["mileage_raw"].str.replace(',', ''), errors='coerce')
    dataframe["satisfaction"] = dataframe["satisfaction_raw"]
    dataframe["reviewCount"] = dataframe["reviewCount_raw"]
    dataframe["salesPoint"] = dataframe["salesPoint_raw"]

    # mappings = [
    #     ("inquiry_type", "inquiry_type_raw", "raw_value"),
    #     ("priority", "priority_raw", "raw_value"),
    #     ("answer_status", "answer_status_raw", "raw_value"),
    #     ("country", "country_name_raw", "raw_country_name"),
    # ]
    # for reference_name, left_column, right_column in mappings:
    #     dataframe = (
    #         dataframe.merge(
    #             references[reference_name],
    #             how="left",
    #             left_on=left_column,
    #             right_on=right_column,
    #         ).drop(columns=[right_column])
    #     )

    # dataframe["product_code"] = dataframe["product_code_raw"].str.upper()
    # dataframe["product_name"] = dataframe["product_name_raw"]
    # product_reference = references["product"].rename(
    #     columns={"product_name": "reference_product_name"}
    # )
    # dataframe = dataframe.merge(product_reference, how="left", on="product_code")

    # dataframe["priority_level"] = pd.to_numeric(
    #     dataframe["priority_level"], errors="coerce"
    # ).astype("Int64")
    # dataframe["collected_at"] = pd.to_datetime(
    #     dataframe["collected_at"], errors="coerce"
    # )
    # dataframe["standardized_at"] = pd.Timestamp.now().floor("s")
    return dataframe