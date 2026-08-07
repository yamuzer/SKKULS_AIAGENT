# 데이터베이스 검증
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    Engine,
    URL,
    create_engine,
    text
)

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'
DATA_PATH = BASE_DIR / 'data' / 'valid_inquiry_ids.csv'
OUTPUT_DIR = BASE_DIR / 'output'


def load_database_config() -> dict[str, Any]:
    if not ENV_PATH.exists():
        raise FileNotFoundError('.env 파일이 없습니다.')

    load_dotenv(ENV_PATH)

    required_keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]

    missing_keys = [
        key for key in required_keys if not os.getenv(key)
    ]

    if missing_keys:
        missing_text = ", ".join(missing_keys)
        raise ValueError(
            f'.env파일에 다음 설정이 없습니다: {missing_text}'
        )

    return {
        'host': os.environ["DB_HOST"],
        'port': int(os.environ["DB_PORT"]),
        'database': os.environ["DB_NAME"],
        'username': os.environ["DB_USER"],
        'password': os.environ["DB_PASSWORD"]
    }


def create_database_engine(config: dict[str, Any]) -> Engine:
    databse_url = URL.create(
        drivername='postgresql+psycopg',
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )

    return create_engine(databse_url, pool_pre_ping=True)


def print_section(title: str) -> None:
    print()
    print('=' * 80)
    print(title)
    print('=' * 80)


def load_inquiry_dataframe(engine: Engine) -> pd.DataFrame:
    # 증분 upsert 데이터 로딩
    if not DATA_PATH.exists():
        raise FileNotFoundError(f'적재 대상 CSV가 없습니다.')

    query = text(
        """
        SELECT ci.inquiry_id,
               ci.received_at,
               ci.source_customer_code,
               ci.customer_id,
               c.customer_name,
               c.customer_grade,
               ci.country_name,
               ci.channel,
               ci.language_code,
               ci.inquiry_type,
               ci.product_code,
               ci.priority,
               ci.status,
               ci.response_minutes,
               ci.satisfaction_score,
               ci.inquiry_text,
               ci.needs_follow_up,
               ci.sla_limit_minutes,
               ci.sla_breached,
               ci.sla_status,
               ci.loaded_at
        FROM python_lab.customer_inquiry AS ci
                 INNER JOIN python_lab.customer AS c
                            ON ci.customer_id = c.customer_id
        ORDER BY ci.received_at,
                 ci.inquiry_id
        """
    )

    with engine.connect() as connection:
        dataframe = pd.read_sql(
            sql=query,
            con=connection,
            parse_dates=[
                'received_at',
                'loaded_at'
            ]
        )

        dataframe['response_minutes'] = dataframe['response_minutes'].astype('Int64')
        dataframe['satisfaction_score'] = dataframe['satisfaction_score'].astype('Int64')
        dataframe['sla_limit_minutes'] = dataframe['sla_limit_minutes'].astype('Int64')
        dataframe['needs_follow_up'] = dataframe['needs_follow_up'].astype('boolean')
        dataframe['sla_breached'] = dataframe['sla_breached'].astype('boolean')

        return dataframe


def converted_to_python_value(value: Any) -> Any:
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if hasattr(value, 'item'):
        try:
            return value.item()
        except ValueError:
            pass

    return value


def dataframe_to_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for row in dataframe.to_dict(orient='records'):
        converted_row = {key: converted_to_python_value(value)
                         for key, value in row.items()}

        records.append(converted_row)

    return records


def check_target_tables(engine: Engine) -> None:
    query_text = text(
        """
        SELECT 
            to_regclass(
                'python_lab.customer'
            )AS customer_table,

            to_regclass(
                'python_lab.customer_inquiry'
            )AS inquiry_table
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query_text).mappings().one()

    if row['customer_table'] is None:
        raise RuntimeError('python_lab.customer 테이블이 없습니다.')

    if row['inquiry_table'] is None:
        raise RuntimeError('python_lab.customer_inquiry 테이블이 없습니다.')


def load_existing_customer_ids(engine: Engine) -> set[int]:
    query = text(
        """
        SELECT customer_id
        FROM python_lab.customer
        """
    )

    with engine.connect() as connection:
        customer_df = pd.read_sql_query(query, connection)

    return set(
        customer_df['customer_id'].astype('int64').tolist()
    )


def load_existing_inquiry_ids(engine: Engine) -> set[str]:
    query = text(
        """
        SELECT inquiry_id
        FROM python_lab.customer_inquiry
        """
    )

    with engine.connect() as connection:
        customer_df = pd.read_sql_query(query, connection)

    return set(
        customer_df['inquiry_id'].astype('string').tolist()
    )


def separate_upsert_groups(
        dataframe: pd.DataFrame,
        existing_customer_ids: set[int],
        existing_inquiry_ids: set[str]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customer_exists_mask = dataframe['customer_id'].isin(existing_customer_ids)

    missing_customer_df = dataframe[~customer_exists_mask].copy()

    valid_df = dataframe[customer_exists_mask].copy()

    update_mask = valid_df['inquiry_id'].isin(existing_inquiry_ids)
    expected_update_df = valid_df[update_mask].copy()
    expected_insert_df = valid_df[~update_mask].copy()

    return expected_insert_df, expected_update_df, missing_customer_df


def save_result_files(
        new_insert_df: pd.DataFrame,
        missing_customer_df: pd.DataFrame,
        already_loaded_df: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    new_insert_df.to_csv(
        OUTPUT_DIR / 'newly_loaded_inquiries.csv',
        index=False,
        encoding='utf-8',
        date_format='%Y/%m/%d %H:%M:%S'
    )

    missing_customer_df.to_csv(
        OUTPUT_DIR / 'missing_customer_inquiries.csv',
        index=False,
        encoding='utf-8',

        date_format='%Y/%m/%d %H:%M:%S'
    )

    already_loaded_df.to_csv(
        OUTPUT_DIR / 'already_loaded_inquiries.csv',
        index=False,
        encoding='utf-8',
        date_format='%Y/%m/%d %H:%M:%S'
    )


def find_duplicate_inquiries(
        dataframe: pd.DataFrame
) -> pd.DataFrame:
    duplicate_mask = dataframe['inquiry_id'].duplicated(keep=False)

    return dataframe[duplicate_mask].sort_values('inquiry_id').copy()


def find_invalid_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    '''
    업무 유효 범위를 벗어낫 데이터를 찾음
    '''

    valid_priorities = {
        'LOW',
        'MEDIUM',
        'HIGH',
        'URGENT'
    }

    valid_statuses = {
        'received',
        'in_progress',
        'resolved',
        'closed'
    }

    valid_sla_statuses = {
        'met',
        'pending',
        'breached'
    }

    invalid_response_mask = (
            dataframe['response_minutes'].notna()
            &
            dataframe['response_minutes'].lt(0)  # dataframe['response_minutes] <0
    )

    invalid_satisfaction_mask = (
            dataframe['satisfaction_score'].notna()
            &
            ~dataframe['satisfaction_score'].between(1, 5, inclusive='both')
    )

    invalid_status_mask = (
        ~dataframe['status'].isin(valid_statuses)
    )

    invalid_sla_status_mask = (
        ~dataframe['sla_status'].isin(valid_sla_statuses)
    )

    invalid_priority_mask = (
        ~dataframe['priority'].isin(valid_priorities)
    )

    invalid_mask = (
            invalid_response_mask
            | invalid_satisfaction_mask
            | invalid_priority_mask
            | invalid_status_mask
            | invalid_sla_status_mask
    )

    return dataframe[invalid_mask].copy()


def build_validation_summary(
        inquiry_df: pd.DataFrame,
        duplicated_df: pd.DataFrame,
        invalid_df: pd.DataFrame,
) -> pd.DataFrame:
    metrics = [
        [
            'total_row_count',
            len(inquiry_df),
            'db에서 읽은 전체 문의 수'
        ],
        [
            'unique_inquiry_count',
            int(inquiry_df['inquiry_id'].nunique()),
            '고유 문의번호 수'
        ],
        [
            'duplicate_row_count',
            len(duplicated_df),
            '중복 inquiry_id에 포함된 행 수'
        ],
        [
            'invalid_row_count',
            len(invalid_df),
            '업무 유효 범위 오류 행 수'
        ],
        [
            'null_response_count',
            int(inquiry_df['response_minutes'].isna().sum()),
            '응답 시간 미기록 문의 수'
        ],
        [
            'null_satisfaction_count',
            int(inquiry_df['satisfaction_score'].isna().sum()),
            '만족도 미기록 문의 수'
        ],
    ]

    return pd.DataFrame(
        metrics,
        columns=[
            'metric_name',
            'metric_value',
            'description',
        ]
    )


def main() -> None:
    engine: Engine | None = None
    try:

        config = load_database_config()
        engine = create_database_engine(config)

        print_section('1. 필수 테이블 확인')

        check_target_tables(engine)

        print_section('2. postgreSQL 데이터를 Dataframe으로 조회')

        inquiry_df = load_inquiry_dataframe(engine)

        print('죄회 데이터 크기: ', inquiry_df.shape)
        print(inquiry_df.iloc[0])

        print('3. 문의번호 중복 확인')

        duplicated_df = find_duplicate_inquiries(inquiry_df)
        print(f'중복 inquiry_id 포함 행 수: {len(duplicated_df)}')

        print_section('4. 업무 유효 범위 확인')

        invalid_df = find_invalid_rows(inquiry_df)

        print(f'유효 범위 오류 행 수: {len(invalid_df)}')

        valid_summary_df = build_validation_summary(
            inquiry_df,
            duplicated_df,
            invalid_df
        )

        print(valid_summary_df.to_string(index=False))

        valid_summary_df.to_csv(
            OUTPUT_DIR / 'validation_summary.csv',
            index=False,
            encoding='utf-8-sig'
        )

    except (
            FileNotFoundError,
            ValueError,
            RuntimeError
    ) as error:
        print('[실행 오류]')
        print(error)
        sys.exit(1)

    except SQLAlchemyError as error:
        print(f'[SQLAlchemy 또는 PostgreSQL 오류]: {error}')
        sys.exit(1)

    except Exception as error:
        print(f'[예상하지 못한 오류]: {error}')
        sys.exit(1)

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()