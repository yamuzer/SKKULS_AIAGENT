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
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

TARGET_SCHEMA = "sqlalchemy_review"
TARGET_TABLE = "customer_inquiry"

VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}
VALID_STATUSES = {"received", "in_progress", "resolved", "closed"}
VALID_SLA_STATUSES = {"met", "pending", "breached"}


def load_database_config() -> dict[str, Any]:
    if not ENV_PATH.exists():
        raise FileNotFoundError(".env 파일이 없습니다.")

    load_dotenv(ENV_PATH)

    required_keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_keys = [key for key in required_keys if not os.getenv(key)]

    if missing_keys:
        raise ValueError(
            ".env 파일에 다음 설정이 없습니다: "
            + ", ".join(missing_keys)
        )

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "database": os.environ["DB_NAME"],
        "username": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


def create_database_engine(config: dict[str, Any]) -> Engine:
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )

    return create_engine(database_url, pool_pre_ping=True)


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def load_source_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"입력 CSV가 없습니다: {path}")

    return pd.read_csv(
        path,
        encoding="utf-8-sig",
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
            "sla_status": "string",
        },
        parse_dates=["received_at"],
    )


def prepare_database_payload(source_df: pd.DataFrame) -> pd.DataFrame:
    payload_df = source_df.copy()

    payload_df["source_customer_code"] = (
        payload_df["customer_id"].astype("string")
    )

    extracted_customer_id = (
        payload_df["source_customer_code"]
        .str.extract(r"^CUST-(\d{4})$", expand=False)
    )

    payload_df["customer_id"] = pd.to_numeric(
        extracted_customer_id,
        errors="coerce",
    ).astype("Int64")

    payload_df["product_code"] = payload_df["product_code"].replace(
        {"NO_PRODUCT": pd.NA}
    )

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
        "sla_status",
    ]

    return payload_df[selected_columns].copy()


def add_rejection_reasons(
    payload_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dataframe = payload_df.copy()
    reasons = pd.Series("", index=dataframe.index, dtype="string")

    invalid_customer_mask = dataframe["customer_id"].isna()
    duplicate_mask = dataframe["inquiry_id"].duplicated(keep=False)

    invalid_response_mask = (
        dataframe["response_minutes"].notna()
        & dataframe["response_minutes"].lt(0)
    )

    invalid_satisfaction_mask = (
        dataframe["satisfaction_score"].notna()
        & ~dataframe["satisfaction_score"].between(1, 5, inclusive="both")
    )

    invalid_priority_mask = ~dataframe["priority"].isin(VALID_PRIORITIES)
    invalid_status_mask = ~dataframe["status"].isin(VALID_STATUSES)
    invalid_sla_status_mask = ~dataframe["sla_status"].isin(
        VALID_SLA_STATUSES
    )

    checks = [
        (invalid_customer_mask, "고객코드 형식 오류"),
        (duplicate_mask, "중복 inquiry_id"),
        (invalid_response_mask, "응답시간 음수"),
        (invalid_satisfaction_mask, "만족도 범위 오류"),
        (invalid_priority_mask, "우선순위 오류"),
        (invalid_status_mask, "처리상태 오류"),
        (invalid_sla_status_mask, "SLA 상태 오류"),
    ]

    for mask, message in checks:
        current = reasons.loc[mask]
        reasons.loc[mask] = current.where(
            current.eq(""),
            current + "; ",
        ) + message

    dataframe["rejection_reason"] = reasons

    rejected_df = dataframe[
        dataframe["rejection_reason"].ne("")
    ].copy()

    valid_df = dataframe[
        dataframe["rejection_reason"].eq("")
    ].drop(columns=["rejection_reason"]).copy()

    return valid_df, rejected_df


def check_target_tables(engine: Engine) -> None:
    query = text(
        """
        SELECT
            to_regclass(
                'sqlalchemy_review.customer'
            ) AS customer_table,
            to_regclass(
                'sqlalchemy_review.customer_inquiry'
            ) AS inquiry_table
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query).mappings().one()

    if row["customer_table"] is None:
        raise RuntimeError(
            "sqlalchemy_review.customer 테이블이 없습니다."
        )

    if row["inquiry_table"] is None:
        raise RuntimeError(
            "sqlalchemy_review.customer_inquiry 테이블이 없습니다."
        )


def load_existing_customer_ids(engine: Engine) -> set[int]:
    query = text(
        """
        SELECT customer_id
        FROM sqlalchemy_review.customer
        """
    )

    with engine.connect() as connection:
        customer_df = pd.read_sql_query(query, connection)

    return set(customer_df["customer_id"].astype("int64").tolist())


def load_existing_inquiry_ids(engine: Engine) -> set[str]:
    query = text(
        """
        SELECT inquiry_id
        FROM sqlalchemy_review.customer_inquiry
        """
    )

    with engine.connect() as connection:
        inquiry_df = pd.read_sql_query(query, connection)

    return set(inquiry_df["inquiry_id"].astype("string").tolist())


def separate_load_groups(
    dataframe: pd.DataFrame,
    existing_customer_ids: set[int],
    existing_inquiry_ids: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customer_exists_mask = dataframe["customer_id"].isin(
        existing_customer_ids
    )

    missing_customer_df = dataframe[~customer_exists_mask].copy()
    customer_valid_df = dataframe[customer_exists_mask].copy()

    already_loaded_mask = customer_valid_df["inquiry_id"].isin(
        existing_inquiry_ids
    )

    already_loaded_df = customer_valid_df[
        already_loaded_mask
    ].copy()

    new_insert_df = customer_valid_df[
        ~already_loaded_mask
    ].copy()

    return new_insert_df, missing_customer_df, already_loaded_df


def converted_to_python_value(value: Any) -> Any:
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    return value


def dataframe_to_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for row in dataframe.to_dict(orient="records"):
        converted_row = {
            key: converted_to_python_value(value)
            for key, value in row.items()
        }
        records.append(converted_row)

    return records
DATA_PATH = DATA_DIR / "inquiry_insert_target.csv"
PROBLEM_OUTPUT_DIR = OUTPUT_DIR / "problem1"


def insert_dataframe(
    engine: Engine,
    insert_df: pd.DataFrame,
) -> int:
    if insert_df.empty:
        return 0

    with engine.begin() as connection:
        insert_df.to_sql(
            name=TARGET_TABLE,
            schema=TARGET_SCHEMA,
            con=connection,
            if_exists="append",
            index=False,
            chunksize=100,
            method="multi",
        )

    return len(insert_df)


def save_result_files(
    new_insert_df: pd.DataFrame,
    missing_customer_df: pd.DataFrame,
    already_loaded_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
) -> None:
    PROBLEM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result_map = {
        "newly_loaded_inquiries.csv": new_insert_df,
        "missing_customer_inquiries.csv": missing_customer_df,
        "already_loaded_inquiries.csv": already_loaded_df,
        "rejected_inquiries.csv": rejected_df,
    }

    for filename, dataframe in result_map.items():
        dataframe.to_csv(
            PROBLEM_OUTPUT_DIR / filename,
            index=False,
            encoding="utf-8-sig",
            date_format="%Y-%m-%d %H:%M:%S",
        )

    summary_df = pd.DataFrame(
        [
            ["source_row_count",
             len(new_insert_df)
             + len(missing_customer_df)
             + len(already_loaded_df)
             + len(rejected_df),
             "입력 CSV 전체 행 수"],
            ["new_insert_count", len(new_insert_df), "신규 적재 행 수"],
            ["missing_customer_count", len(missing_customer_df), "미등록 고객 행 수"],
            ["already_loaded_count", len(already_loaded_df), "기존 문의 행 수"],
            ["rejected_count", len(rejected_df), "입력 오류 행 수"],
        ],
        columns=["metric_name", "metric_value", "description"],
    )

    summary_df.to_csv(
        PROBLEM_OUTPUT_DIR / "load_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )


def main() -> None:
    engine: Engine | None = None

    try:
        print_section("1. CSV 읽기와 전처리")

        source_df = load_source_csv(DATA_PATH)
        payload_df = prepare_database_payload(source_df)
        valid_df, rejected_df = add_rejection_reasons(payload_df)

        print(f"입력 행 수: {len(source_df)}")
        print(f"검증 통과 행 수: {len(valid_df)}")
        print(f"입력 오류 행 수: {len(rejected_df)}")

        config = load_database_config()
        engine = create_database_engine(config)

        print_section("2. DB 기준정보 확인")

        check_target_tables(engine)
        existing_customer_ids = load_existing_customer_ids(engine)
        existing_inquiry_ids = load_existing_inquiry_ids(engine)

        print(f"기존 고객 수: {len(existing_customer_ids)}")
        print(f"기존 문의 수: {len(existing_inquiry_ids)}")

        print_section("3. 적재 그룹 분리")

        new_insert_df, missing_customer_df, already_loaded_df = (
            separate_load_groups(
                valid_df,
                existing_customer_ids,
                existing_inquiry_ids,
            )
        )

        print(f"신규 적재 대상: {len(new_insert_df)}")
        print(f"미등록 고객: {len(missing_customer_df)}")
        print(f"기존 문의: {len(already_loaded_df)}")

        print_section("4. 신규 문의 적재")

        inserted_count = insert_dataframe(engine, new_insert_df)
        print(f"실제 적재 행 수: {inserted_count}")

        print_section("5. 결과 파일 저장")

        save_result_files(
            new_insert_df,
            missing_customer_df,
            already_loaded_df,
            rejected_df,
        )

        print(f"결과 폴더: {PROBLEM_OUTPUT_DIR}")

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        print("[실행 오류]")
        print(error)
        sys.exit(1)

    except SQLAlchemyError as error:
        print(f"[SQLAlchemy 또는 PostgreSQL 오류]: {error}")
        sys.exit(1)

    except Exception as error:
        print(f"[예상하지 못한 오류]: {error}")
        sys.exit(1)

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
