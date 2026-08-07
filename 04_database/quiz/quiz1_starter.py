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
    """
    TODO
    1. 빈 DataFrame이면 0을 반환합니다.
    2. engine.begin()으로 트랜잭션을 시작합니다.
    3. DataFrame.to_sql()로 신규 문의를 append합니다.
    4. 실제 적재 행 수를 반환합니다.
    """
    raise NotImplementedError


def save_result_files(
    new_insert_df: pd.DataFrame,
    missing_customer_df: pd.DataFrame,
    already_loaded_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
) -> None:
    """
    TODO
    output/problem1 폴더를 생성하고 결과 CSV 5개를 저장합니다.
    """
    raise NotImplementedError


def main() -> None:
    engine: Engine | None = None

    try:
        print_section("1. CSV 읽기와 전처리")

        # TODO: CSV 읽기
        # TODO: DB 적재용 DataFrame 생성
        # TODO: 정상 행과 오류 행 분리

        config = load_database_config()
        engine = create_database_engine(config)

        print_section("2. DB 기준정보 확인")

        # TODO: 테이블 확인
        # TODO: 기존 고객번호와 문의번호 조회

        print_section("3. 적재 그룹 분리")

        # TODO: 신규, 미등록 고객, 기존 문의로 분리

        print_section("4. 신규 문의 적재")

        # TODO: 신규 문의만 적재

        print_section("5. 결과 파일 저장")

        # TODO: 결과 파일 저장

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
