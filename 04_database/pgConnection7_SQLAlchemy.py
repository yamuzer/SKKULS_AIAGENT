# 데이터프레임을 데이터베이스에 임포트
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'
DATA_PATH = BASE_DIR / 'data' / 'inquiry_insert_target.csv'
OUTPUT_DIR = BASE_DIR / 'output'

TARGET_SCHEMA = 'python_lab'
TARGET_TABLE = 'customer_inquiry'


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


def load_target_csv() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f'적재 대상 CSV가 없습니다.')

    return pd.read_csv(
        DATA_PATH,
        encoding='utf-8-sig',
        dtype={
            "inquiry_id": "string",
            "customer_id": "string",
            "channel": "string",
            "language_code": "string",
            "country_name": "string",
            "inquiry_type": "string",
            "product_code": "string",
            "priority": "string",
            "status": "string",
            "response_minutes": "Int64",
            "satisfaction_score": "Int64",
            "inquiry_text": "string",
            "needs_follow_up": "boolean",
            "sla_limit_minutes": "Int64",
            "sla_breached": "boolean",
            "sla_status": "string"
        },
        parse_dates=["received_at"]
    )


def prepare_database_payload(source_df: pd.DataFrame) -> pd.DataFrame:

    payload_df = source_df.copy()

    payload_df['source_customer_code'] = payload_df['customer_id'].astype('string')

    # CUST-0001 => 0001
    # CUSTOMER-1234 => NAN
    # CUST-12 => NAN
    extract_id = payload_df['source_customer_code'].str.extract(
        r"CUST-(\d{4})",
        expand=False
    )

    payload_df['customer_id'] = pd.to_numeric(extract_id, errors='coerce').astype('Int64')
    payload_df['product_code'] = payload_df['product_code'].replace({'NO_PRODUCT': pd.NA})

    selected_columns = [
        "inquiry_id",
        "source_customer_code",
        "customer_id",
        "received_at",
        "channel",
        "language_code",
        "country_name",
        "inquiry_type",
        "product_code",
        "priority",
        "status",
        "response_minutes",
        "satisfaction_score",
        "inquiry_text",
        "needs_follow_up",
        "sla_limit_minutes",
        "sla_breached",
        "sla_status"
    ]

    payload_df = payload_df[selected_columns].copy()

    if payload_df['customer_id'].isna().any():
        count = int(payload_df['customer_id'].sum())
        raise ValueError(f'고객번호 변환 실패: {count}')

    if payload_df['inquiry_id'].duplicated().any():
        count = int(payload_df['inquiry_id'].duplicated().sum())
        raise ValueError(f'중복 inquiry_id: {count}')

    return payload_df


def check_target_table(engine: Engine) -> None:
    query_text = text(
        """
        SELECT 
            to_regclass(
                'python_lab.customer_inquiry'
            )AS target_table
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query_text).mappings().one()

    if row['target_table'] is None:
        raise RuntimeError('python_lab.customer_inquiry가 없습니다.')


def load_existing_customer_ids(engine:Engine) -> set[int]:
    query= text(
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


def sepearate_load_groups(
    payload_df: pd.DataFrame,
    customer_ids: set[int],
    inquiry_ids: set[str]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customer_exists_mask = payload_df['customer_id'].isin(customer_ids)

    missing_customer_df = payload_df[~customer_exists_mask].copy()

    customer_valid_df = payload_df[customer_exists_mask].copy()

    already_loaded_mask = customer_valid_df['inquiry_id'].isin(inquiry_ids)
    already_loaded_df = customer_valid_df[already_loaded_mask].copy()
    new_insert_df = customer_valid_df[~already_loaded_mask].copy()

    return new_insert_df, missing_customer_df, already_loaded_df


def insert_dataframe(
    engine: Engine,
    insert_df: pd.DataFrame,
) -> int:

    if insert_df.empty:
        return 0

    with engine.connect() as connection:
        insert_df.to_sql(
            name=TARGET_TABLE,
            schema=TARGET_SCHEMA,
            con=connection,
            if_exists='append',
            index=False,
            chunksize=100,
            method='multi'
        )

    return len(insert_df)


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


def main() -> None:

    engine: Engine | None = None
    try:
        print_section('적재 대상 읽기')
        source_df = load_target_csv()
        # print('csv 적제 대상: ', len(source_df))
        # print(source_df.head())
        # source_df.info()
        #print(source_df.iloc[0])

        payload_df = prepare_database_payload(source_df)
        #print(payload_df.iloc[0])

        config = load_database_config()
        engine = create_database_engine(config)

        print_section('테이블과 기존 데이터 확인')
        check_target_table(engine)

        customer_ids = load_existing_customer_ids(engine)

        inquiry_ids = load_existing_inquiry_ids(engine)

        print_section('적재 그룹 분리')

        new_insert_df, missing_customer_df, already_loaded_df = sepearate_load_groups(
            payload_df,
            customer_ids,
            inquiry_ids
        )

        print_section('dataframe 적재')

        inserted_count = insert_dataframe(
            engine,
            new_insert_df
        )

        save_result_files(
            new_insert_df,
            missing_customer_df,
            already_loaded_df
        )


    except (
        FileNotFoundError,
        ValueError,
        RuntimeError
    )as error:
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