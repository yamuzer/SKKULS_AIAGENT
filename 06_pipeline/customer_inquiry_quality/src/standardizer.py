from __future__ import annotations

from datetime import datetime
import pandas as pd

DATE_FORMAT = [
    '%Y-%m-%d %H:%M',
    '%Y/%m/%d %H:%M',
    '%d-%m-%Y %H:%M',
    '%Y.%m.%d %H:%M',
]

def clean_text_series(series: pd.Series) -> pd.Series:

    return (
        series
        .fillna('')
        .astype("string")
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
    )


def parse_mixed_datetime(value: str):

    value = str(value).strip()

    if not value:
        return pd.NaT

    for date_format in DATE_FORMAT:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    return pd.NaT



def standardize_inquiries(
    raw_df: pd.DataFrame,
    references: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    '''
    원천 문자열을 표준 열과 기준 정보 코드로 변환
    '''

    standardized_df = raw_df.copy()

    text_columns = [
        'source_inquiry_id',
        'author_name_raw',
        'country_name_raw',
        'language_code_raw',
        'posted_at_raw',
        'inquiry_type_raw',
        'priority_raw',
        'product_code_raw',
        'product_name_raw',
        'answer_status_raw',
        'inquiry_title_raw',
        'inquiry_text_raw',
        'source_url'
    ]

    for column in text_columns:
        standardized_df[column] = clean_text_series(standardized_df[column])

    standardized_df['source_inquiry_id'] = standardized_df['source_inquiry_id'].str.upper()

    standardized_df['author_name'] = standardized_df['author_name_raw']

    standardized_df['posted_at'] = standardized_df['posted_at_raw'].map(parse_mixed_datetime)

    standardized_df['inquiry_title'] = standardized_df['inquiry_title_raw']

    standardized_df['inquiry_text'] = standardized_df['inquiry_text_raw']

    standardized_df['language_code'] = standardized_df['language_code_raw'].str.strip()

    standardized_df = (standardized_df.merge(references['inquiry_type'],
                                            how='left',
                                            left_on='inquiry_type_raw',
                                            right_on='raw_value'
                                            ).
                                            drop(columns='raw_value')
    )

    standardized_df = (standardized_df.merge(references['priority'],
                                             how='left',
                                             left_on='priority_raw',
                                             right_on='raw_value'
                                             ).
                                             drop(columns='raw_value')
                       )

    standardized_df = (standardized_df.merge(references['answer_status'],
                                             how='left',
                                             left_on='answer_status_raw',
                                             right_on='raw_value'
                                             ).
                                             drop(columns='raw_value')
                       )

    standardized_df = (standardized_df.merge(references['country'],
                                             how='left',
                                             left_on='country_name_raw',
                                             right_on='raw_country_name'
                                             ).
                                             drop(columns='raw_country_name')
                       )

    product_reference = references['product'].rename(
        columns={
            'product_name': 'reference_product_name',
        }
    )


    standardized_df['product_code'] = standardized_df['product_code_raw'].str.upper()

    standardized_df['product_name'] = standardized_df['product_name_raw']

    standardized_df = standardized_df.merge(product_reference, how='left', on='product_code')

    standardized_df['priority_level'] = pd.to_numeric(standardized_df['priority_level'], errors='coerce').astype('Int64')

    standardized_df['collected_at'] = pd.to_datetime(standardized_df['collected_at'], errors='coerce')

    standardized_df['standardized_at'] = pd.Timestamp.now().floor('s')

    result_columns = [
        'source_inquiry_id',
        'author_name_raw',
        'author_name',
        'country_name_raw',
        'country_code',
        'country_name',
        'language_code_raw',
        'language_code',
        'default_language_code',
        'posted_at_raw',
        'posted_at',
        'inquiry_type_raw',
        'inquiry_type_code',
        'inquiry_type_name',
        'priority_raw',
        'priority_code',
        'priority_level',
        'product_code_raw',
        'product_code',
        'product_name_raw',
        'product_name',
        'reference_product_name',
        'product_category_code',
        'answer_status_raw',
        'answer_status_code',
        'answer_status_name',
        'inquiry_title_raw',
        'inquiry_title',
        'inquiry_text_raw',
        'inquiry_text',
        'source_url',
        'collected_at',
        'standardized_at'
    ]

    return standardized_df[result_columns]














