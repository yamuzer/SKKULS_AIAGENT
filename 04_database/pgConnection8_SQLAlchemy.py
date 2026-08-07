# 증분 임포트 및 검증

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


import pandas as pd
import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import (
    Engine,
    MetaData,
    Table,
    URL,
    create_engine,
    func,
    select,
    text
)

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'
DATA_PATH = BASE_DIR / 'data' / 'customer_inquiry_incremental.csv'
OUTPUT_DIR = BASE_DIR / 'output'

TARGET_SCHEMA = 'python_lab'
TARGET_TABLE = 'customer_inquiry'
CHUNK_SIZE = 50


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


def load_incremental_data() -> pd.DataFrame:
    #증분 upsert 데이터 로딩
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

    records : list[dict[str, Any]] = []

    for row in dataframe.to_dict(orient='records'):
        converted_row = {key: converted_to_python_value(value)
                         for key, value in row.items()}

        records.append(converted_row)

    return records


def upsert_dataframe(
        engine: Engine,
        dataframe: pd.DataFrame,
) -> int:

    if dataframe.empty:
        return 0

    update_columns_names = [
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

    processed_count = 0

    with engine.connect() as connection:
        metadata = MetaData()

        target_table = Table(
            TARGET_TABLE,
            metadata,
            schema=TARGET_SCHEMA,
            autoload_with=connection
        )

        for start_index in range(0, len(dataframe), CHUNK_SIZE):
            chunk_df = dataframe.iloc[start_index:start_index + CHUNK_SIZE]

            records = dataframe_to_records(chunk_df)

            insert_statement = pg_insert(target_table).values(records)

            update_value = {
                column_name: insert_statement.excluded[column_name] for column_name in update_columns_names
            }

            update_value['located_at'] = func.current_timestamp()

            upsert_statement = insert_statement.on_conflict_do_update(
                index_elements=[target_table.c.inquiry_id],
                set=update_value
            )

            connection.execute(upsert_statement)

            processed_count += 1

        return processed_count




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

def load_upserted_rows(
    engine: Engine,
    inquiry_ids: list[str],
) -> pd.DataFrame:
    '''
    upsert 대상 문의를 db에서 다시 조회
    '''

    if not inquiry_ids:
        return pd.DataFrame()

    metadata = MetaData()

    with engine.connect() as connection:
        target_table = Table(
            TARGET_TABLE,
            metadata,
             schema=TARGET_SCHEMA,
            autoload_with=connection
        )

        query = text(
            select(target_table)
            .where(
                target_table.c.inquiry_id.in_(inquiry_ids)
            )
            .order_by(
                target_table.c.inquiry_id
            )
        )

        result = connection.execute(query)
        rows = result.mappings().all()

    return pd.DataFrame(rows)

def main() -> None:

    engine: Engine | None = None
    try:
        print_section('1. 증분 데이터 읽기')

        incremental_df = load_incremental_data()
        '''
        print(len(incremental_df))
        incremental_df.info()
        '''

        config = load_database_config()
        engine = create_database_engine(config)

        print_section('2. 현재 DB 상태 확인')

        existing_customer_ids = load_existing_customer_ids(engine)
        existing_inquiry_ids = load_existing_inquiry_ids(engine)

        check_target_table(engine)
        print(f'현재 customer 고객 수: {len(existing_customer_ids)}')
        print(f'현재 customer_inquiry 문의 수: {len(existing_inquiry_ids)}')

        expected_insert_df, expected_update_df, missing_customer_df = separate_upsert_groups(
            dataframe=incremental_df,
            existing_customer_ids=existing_customer_ids,
            existing_inquiry_ids=existing_inquiry_ids
        )

        print(f'신규 insert 예상: {len(expected_insert_df)}')
        print(f'신규 update 예상: {len(expected_update_df)}')
        print(f'고객 없음: {len(missing_customer_df)}')

        valid_upsert_df = pd.concat([expected_insert_df, expected_update_df], ignore_index=True)

        print_section('3. upsert 실행')

        processed_count = upsert_dataframe(
            engine,
            valid_upsert_df
        )

        print('upsert 처리 행 수: ', processed_count)

        upserted_rows_df = load_upserted_rows(
            engine,
            valid_upsert_df['inquiry_id'].tolist()
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