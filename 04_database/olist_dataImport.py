from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    Engine,
    MetaData,
    Table,
    URL,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.exc import SQLAlchemyError


# =============================================================================
# 기본 설정
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

CUSTOMERS_CSV_PATH = BASE_DIR / "data/olist_customers_dataset.csv"
ORDERS_CSV_PATH = BASE_DIR / "data/olist_orders_dataset.csv"

SCHEMA_NAME = "olist_schema"
CUSTOMERS_TABLE_NAME = "olist_customers"
ORDERS_TABLE_NAME = "olist_orders"

INSERT_CHUNK_SIZE = 2_000


# =============================================================================
# 공통 함수
# =============================================================================

def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def load_database_config() -> dict[str, Any]:
    """환경변수에서 PostgreSQL 접속 정보를 불러온다."""

    if not ENV_PATH.exists():
        raise FileNotFoundError(
            f".env 파일이 없습니다: {ENV_PATH}"
        )

    load_dotenv(
        dotenv_path=ENV_PATH,
        override=True,
    )

    required_keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_keys = [
        key
        for key in required_keys
        if not os.getenv(key)
    ]

    if missing_keys:
        missing_text = ", ".join(missing_keys)

        raise ValueError(
            f".env 파일에 다음 설정이 없습니다: {missing_text}"
        )

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "database": os.environ["DB_NAME"],
        "username": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


def create_database_engine(
    config: dict[str, Any],
) -> Engine:
    """SQLAlchemy Engine을 생성한다."""

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


# =============================================================================
# 파일 및 DB 구조 검증
# =============================================================================

def validate_csv_files() -> None:
    """필요한 CSV 파일이 존재하는지 확인한다."""

    required_paths = [
        CUSTOMERS_CSV_PATH,
        ORDERS_CSV_PATH,
    ]

    missing_files = [
        path.name
        for path in required_paths
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "다음 CSV 파일이 없습니다: "
            + ", ".join(missing_files)
        )


def check_database_connection(engine: Engine) -> None:
    """현재 연결된 DB와 사용자를 출력한다."""

    query = text(
        """
        SELECT
            current_database() AS database_name,
            current_schema() AS current_schema_name,
            current_user AS user_name
        """
    )

    with engine.connect() as connection:
        result = connection.execute(query).mappings().one()

    print_section("PostgreSQL 연결 정보")
    print(f"연결된 DB:     {result['database_name']}")
    print(f"기본 스키마:  {result['current_schema_name']}")
    print(f"접속 사용자:  {result['user_name']}")

    if result["database_name"] != "olist_db":
        raise ValueError(
            "olist_db가 아닌 다른 데이터베이스에 연결되었습니다. "
            ".env의 DB_NAME을 확인하세요."
        )


def validate_database_structure(engine: Engine) -> None:
    """스키마와 대상 테이블이 미리 생성되어 있는지 확인한다."""

    inspector = inspect(engine)

    if not inspector.has_schema(SCHEMA_NAME):
        raise ValueError(
            f"{SCHEMA_NAME} 스키마가 없습니다."
        )

    required_tables = [
        CUSTOMERS_TABLE_NAME,
        ORDERS_TABLE_NAME,
    ]

    missing_tables = [
        table_name
        for table_name in required_tables
        if not inspector.has_table(
            table_name=table_name,
            schema=SCHEMA_NAME,
        )
    ]

    if missing_tables:
        raise ValueError(
            f"{SCHEMA_NAME}에 다음 테이블이 없습니다: "
            + ", ".join(missing_tables)
        )

    print_section("DB 구조 확인")
    print(f"스키마 확인: {SCHEMA_NAME}")

    for table_name in required_tables:
        print(f"테이블 확인: {SCHEMA_NAME}.{table_name}")


def validate_columns(
    dataframe: pd.DataFrame,
    expected_columns: list[str],
    file_name: str,
) -> None:
    """CSV에 필요한 컬럼이 모두 존재하는지 확인한다."""

    missing_columns = [
        column
        for column in expected_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{file_name}에 다음 컬럼이 없습니다: "
            + ", ".join(missing_columns)
        )


# =============================================================================
# CSV 로드
# =============================================================================

def load_customers_csv() -> pd.DataFrame:
    """고객 CSV를 DataFrame으로 불러온다."""

    customer_df = pd.read_csv(
        CUSTOMERS_CSV_PATH,
        dtype={
            "customer_id": "string",
            "customer_unique_id": "string",
            # 09790과 같은 앞자리 0을 보존한다.
            "customer_zip_code_prefix": "string",
            "customer_city": "string",
            "customer_state": "string",
        },
        encoding="utf-8",
    )

    expected_columns = [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ]

    validate_columns(
        dataframe=customer_df,
        expected_columns=expected_columns,
        file_name=CUSTOMERS_CSV_PATH.name,
    )

    customer_df = customer_df[expected_columns].copy()

    return customer_df


def load_orders_csv() -> pd.DataFrame:
    """주문 CSV를 DataFrame으로 불러온다."""

    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    order_df = pd.read_csv(
        ORDERS_CSV_PATH,
        dtype={
            "order_id": "string",
            "customer_id": "string",
            "order_status": "string",
        },
        parse_dates=date_columns,
        encoding="utf-8",
    )

    expected_columns = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    validate_columns(
        dataframe=order_df,
        expected_columns=expected_columns,
        file_name=ORDERS_CSV_PATH.name,
    )

    order_df = order_df[expected_columns].copy()

    return order_df


def validate_csv_dataframes(
    customer_df: pd.DataFrame,
    order_df: pd.DataFrame,
) -> None:
    """입력 전 CSV의 필수값과 기본키 중복을 검사한다."""

    customer_required_columns = [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ]

    order_required_columns = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_estimated_delivery_date",
    ]

    customer_null_count = int(
        customer_df[customer_required_columns]
        .isna()
        .any(axis=1)
        .sum()
    )

    order_null_count = int(
        order_df[order_required_columns]
        .isna()
        .any(axis=1)
        .sum()
    )

    customer_duplicate_count = int(
        customer_df["customer_id"].duplicated().sum()
    )

    order_duplicate_count = int(
        order_df["order_id"].duplicated().sum()
    )

    csv_customer_ids = set(
        customer_df["customer_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    csv_order_customer_ids = set(
        order_df["customer_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    missing_customer_ids = (
        csv_order_customer_ids - csv_customer_ids
    )

    print_section("CSV 데이터 검증")
    print(f"고객 CSV 행 수:          {len(customer_df):,}")
    print(f"주문 CSV 행 수:          {len(order_df):,}")
    print(f"고객 필수값 오류:        {customer_null_count:,}")
    print(f"주문 필수값 오류:        {order_null_count:,}")
    print(f"고객 기본키 중복:        {customer_duplicate_count:,}")
    print(f"주문 기본키 중복:        {order_duplicate_count:,}")
    print(f"고객 정보가 없는 주문:   {len(missing_customer_ids):,}")

    if customer_null_count > 0:
        raise ValueError(
            "고객 CSV의 NOT NULL 컬럼에 결측값이 있습니다."
        )

    if order_null_count > 0:
        raise ValueError(
            "주문 CSV의 NOT NULL 컬럼에 결측값이 있습니다."
        )

    if customer_duplicate_count > 0:
        raise ValueError(
            "고객 CSV에 중복 customer_id가 있습니다."
        )

    if order_duplicate_count > 0:
        raise ValueError(
            "주문 CSV에 중복 order_id가 있습니다."
        )

    if missing_customer_ids:
        raise ValueError(
            "주문 CSV에 고객 CSV에 존재하지 않는 "
            "customer_id가 있습니다."
        )


# =============================================================================
# PostgreSQL 입력
# =============================================================================

def dataframe_to_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    DataFrame을 INSERT 가능한 딕셔너리 목록으로 변환한다.

    NaN과 NaT는 PostgreSQL NULL에 대응되는 None으로 변환한다.
    """

    clean_df = dataframe.astype(object).where(
        pd.notna(dataframe),
        None,
    )

    return clean_df.to_dict(orient="records")


def insert_dataframe_ignore_duplicates(
    engine: Engine,
    dataframe: pd.DataFrame,
    table_name: str,
    primary_key: str,
) -> int:
    """
    DataFrame을 PostgreSQL에 입력한다.

    기본키가 이미 존재하면 해당 행은 건너뛴다.
    따라서 프로그램을 재실행해도 기본키 중복 오류가 발생하지 않는다.
    """

    metadata = MetaData()

    table = Table(
        table_name,
        metadata,
        schema=SCHEMA_NAME,
        autoload_with=engine,
    )

    records = dataframe_to_records(dataframe)

    inserted_count = 0

    with engine.begin() as connection:
        for start_index in range(
            0,
            len(records),
            INSERT_CHUNK_SIZE,
        ):
            chunk = records[
                start_index:
                start_index + INSERT_CHUNK_SIZE
            ]

            statement = (
                postgresql_insert(table)
                .values(chunk)
                .on_conflict_do_nothing(
                    index_elements=[primary_key]
                )
            )

            result = connection.execute(statement)

            if result.rowcount is not None:
                inserted_count += result.rowcount

    skipped_count = len(dataframe) - inserted_count

    print(f"{SCHEMA_NAME}.{table_name}")
    print(f"  CSV 데이터:      {len(dataframe):,}건")
    print(f"  신규 입력:       {inserted_count:,}건")
    print(f"  기존 데이터:     {skipped_count:,}건")

    return inserted_count


def import_csv_data(
    engine: Engine,
    customer_df: pd.DataFrame,
    order_df: pd.DataFrame,
) -> None:
    """고객과 주문 데이터를 순서대로 입력한다."""

    print_section("PostgreSQL 데이터 입력")

    # 외래키 관계 때문에 고객을 먼저 입력한다.
    insert_dataframe_ignore_duplicates(
        engine=engine,
        dataframe=customer_df,
        table_name=CUSTOMERS_TABLE_NAME,
        primary_key="customer_id",
    )

    print()

    insert_dataframe_ignore_duplicates(
        engine=engine,
        dataframe=order_df,
        table_name=ORDERS_TABLE_NAME,
        primary_key="order_id",
    )


# =============================================================================
# 입력 결과 검증
# =============================================================================

def normalize_key_series(
    series: pd.Series,
) -> pd.Series:
    """PostgreSQL CHAR 타입의 좌우 공백을 제거한다."""

    return (
        series
        .dropna()
        .astype(str)
        .str.strip()
    )


def verify_table_import(
    engine: Engine,
    csv_dataframe: pd.DataFrame,
    table_name: str,
    primary_key: str,
) -> bool:
    """CSV와 PostgreSQL 테이블의 기본키를 전수 비교한다."""

    query = text(
        f"""
        SELECT TRIM({primary_key}) AS {primary_key}
        FROM {SCHEMA_NAME}.{table_name}
        """
    )

    with engine.connect() as connection:
        database_df = pd.read_sql_query(
            sql=query,
            con=connection,
        )

    csv_key_series = normalize_key_series(
        csv_dataframe[primary_key]
    )

    database_key_series = normalize_key_series(
        database_df[primary_key]
    )

    csv_keys = set(csv_key_series)
    database_keys = set(database_key_series)

    missing_keys = csv_keys - database_keys
    extra_keys = database_keys - csv_keys

    csv_duplicate_count = int(
        csv_key_series.duplicated().sum()
    )

    database_duplicate_count = int(
        database_key_series.duplicated().sum()
    )

    print_section(f"{table_name} 입력 결과 검증")

    print(f"CSV 전체 행:          {len(csv_dataframe):,}")
    print(f"CSV 고유 PK:          {len(csv_keys):,}")
    print(f"DB 전체 행:           {len(database_df):,}")
    print(f"DB 고유 PK:           {len(database_keys):,}")
    print(f"CSV 중복 PK:          {csv_duplicate_count:,}")
    print(f"DB 중복 PK:           {database_duplicate_count:,}")
    print(f"DB 누락 PK:           {len(missing_keys):,}")
    print(f"CSV에 없는 DB PK:     {len(extra_keys):,}")

    if missing_keys:
        print("\nDB에 입력되지 않은 PK 예시:")

        for key in sorted(missing_keys)[:10]:
            print(f"  - {key}")

    if extra_keys:
        print("\nCSV에는 없지만 DB에 존재하는 PK 예시:")

        for key in sorted(extra_keys)[:10]:
            print(f"  - {key}")

    success = (
        len(csv_dataframe) == len(database_df)
        and len(csv_keys) == len(database_keys)
        and csv_duplicate_count == 0
        and database_duplicate_count == 0
        and len(missing_keys) == 0
        and len(extra_keys) == 0
    )

    if success:
        print(f"\n[성공] {table_name} 데이터가 모두 일치합니다.")
    else:
        print(f"\n[실패] {table_name} 데이터가 일치하지 않습니다.")

    return success


def verify_database_constraints(engine: Engine) -> bool:
    """필수값, 기본키 및 외래키 상태를 검증한다."""

    query = text(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM olist_schema.olist_customers
            ) AS customer_count,

            (
                SELECT COUNT(DISTINCT customer_id)
                FROM olist_schema.olist_customers
            ) AS customer_unique_pk_count,

            (
                SELECT COUNT(*)
                FROM olist_schema.olist_customers
                WHERE customer_id IS NULL
                   OR customer_unique_id IS NULL
                   OR customer_zip_code_prefix IS NULL
                   OR customer_city IS NULL
                   OR customer_state IS NULL
            ) AS invalid_customer_count,

            (
                SELECT COUNT(*)
                FROM olist_schema.olist_orders
            ) AS order_count,

            (
                SELECT COUNT(DISTINCT order_id)
                FROM olist_schema.olist_orders
            ) AS order_unique_pk_count,

            (
                SELECT COUNT(*)
                FROM olist_schema.olist_orders
                WHERE order_id IS NULL
                   OR customer_id IS NULL
                   OR order_status IS NULL
                   OR order_purchase_timestamp IS NULL
                   OR order_estimated_delivery_date IS NULL
            ) AS invalid_order_count,

            (
                SELECT COUNT(*)
                FROM olist_schema.olist_orders AS o
                LEFT JOIN olist_schema.olist_customers AS c
                    ON o.customer_id = c.customer_id
                WHERE c.customer_id IS NULL
            ) AS orphan_order_count
        """
    )

    with engine.connect() as connection:
        result = connection.execute(query).mappings().one()

    print_section("PostgreSQL 제약조건 검증")

    print(f"고객 전체 행:        {result['customer_count']:,}")
    print(f"고객 고유 PK:        {result['customer_unique_pk_count']:,}")
    print(f"고객 필수값 오류:    {result['invalid_customer_count']:,}")
    print(f"주문 전체 행:        {result['order_count']:,}")
    print(f"주문 고유 PK:        {result['order_unique_pk_count']:,}")
    print(f"주문 필수값 오류:    {result['invalid_order_count']:,}")
    print(f"고객 없는 주문:      {result['orphan_order_count']:,}")

    success = (
        result["customer_count"]
        == result["customer_unique_pk_count"]
        and result["order_count"]
        == result["order_unique_pk_count"]
        and result["invalid_customer_count"] == 0
        and result["invalid_order_count"] == 0
        and result["orphan_order_count"] == 0
    )

    if success:
        print("\n[성공] 모든 제약조건이 정상입니다.")
    else:
        print("\n[실패] 제약조건 검증 결과에 문제가 있습니다.")

    return success


def verify_all_data(
    engine: Engine,
    customer_df: pd.DataFrame,
    order_df: pd.DataFrame,
) -> bool:
    """전체 입력 결과를 검증한다."""

    customer_success = verify_table_import(
        engine=engine,
        csv_dataframe=customer_df,
        table_name=CUSTOMERS_TABLE_NAME,
        primary_key="customer_id",
    )

    order_success = verify_table_import(
        engine=engine,
        csv_dataframe=order_df,
        table_name=ORDERS_TABLE_NAME,
        primary_key="order_id",
    )

    constraint_success = verify_database_constraints(
        engine=engine,
    )

    final_success = (
        customer_success
        and order_success
        and constraint_success
    )

    print_section("최종 결과")

    if final_success:
        print(
            "[최종 성공] 고객 및 주문 데이터가 "
            "모두 정상적으로 입력되었습니다."
        )
    else:
        print(
            "[최종 실패] CSV와 PostgreSQL 데이터가 "
            "완전히 일치하지 않습니다."
        )

    return final_success


# =============================================================================
# 프로그램 실행
# =============================================================================

def main() -> None:
    engine: Engine | None = None

    try:
        # 1. CSV 파일 확인
        validate_csv_files()

        # 2. PostgreSQL 연결
        config = load_database_config()
        engine = create_database_engine(config)

        check_database_connection(engine)
        validate_database_structure(engine)

        # 3. CSV 불러오기
        print_section("CSV 파일 읽기")

        customer_df = load_customers_csv()
        order_df = load_orders_csv()

        print(f"고객 데이터: {len(customer_df):,}건")
        print(f"주문 데이터: {len(order_df):,}건")

        # 4. CSV 자체 검증
        validate_csv_dataframes(
            customer_df=customer_df,
            order_df=order_df,
        )

        # 5. PostgreSQL 입력
        import_csv_data(
            engine=engine,
            customer_df=customer_df,
            order_df=order_df,
        )

        # 6. 입력 결과 검증
        final_success = verify_all_data(
            engine=engine,
            customer_df=customer_df,
            order_df=order_df,
        )

        if not final_success:
            sys.exit(1)

    except FileNotFoundError as error:
        print(f"\n[파일 오류] {error}")
        sys.exit(1)

    except ValueError as error:
        print(f"\n[설정 또는 데이터 오류] {error}")
        sys.exit(1)

    except SQLAlchemyError as error:
        print(f"\n[SQLAlchemy 또는 PostgreSQL 오류] {error}")

        # 오류의 원본 PostgreSQL 메시지도 출력한다.
        if getattr(error, "orig", None) is not None:
            print(f"[PostgreSQL 원본 오류] {error.orig}")

        sys.exit(1)

    except Exception as error:
        print(f"\n[예상하지 못한 오류] {error}")
        sys.exit(1)

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()