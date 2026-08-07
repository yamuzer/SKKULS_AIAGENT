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
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"

TARGET_SCHEMA = "sqlalchemy_review"


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


def load_customers() -> pd.DataFrame:
    return pd.read_csv(
        DATA_DIR / "customers.csv",
        encoding="utf-8-sig",
        dtype={
            "customer_id": "int64",
            "customer_code": "string",
            "customer_name": "string",
            "customer_grade": "string",
            "country_name": "string",
        },
    )


def load_base_inquiries() -> pd.DataFrame:
    dataframe = pd.read_csv(
        DATA_DIR / "base_customer_inquiries.csv",
        encoding="utf-8-sig",
        dtype={
            "inquiry_id": "string",
            "source_customer_code": "string",
            "customer_id": "int64",
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

    dataframe["product_code"] = dataframe["product_code"].replace(
        {"": pd.NA}
    )

    return dataframe


def check_tables(engine: Engine) -> None:
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

    if row["customer_table"] is None or row["inquiry_table"] is None:
        raise RuntimeError(
            "먼저 00_create_tables.sql을 실행하세요."
        )


def main() -> None:
    engine: Engine | None = None

    try:
        config = load_database_config()
        engine = create_database_engine(config)
        check_tables(engine)

        customer_df = load_customers()
        inquiry_df = load_base_inquiries()

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    TRUNCATE TABLE
                        sqlalchemy_review.customer_inquiry,
                        sqlalchemy_review.customer
                    RESTART IDENTITY
                    """
                )
            )

            customer_df.to_sql(
                name="customer",
                schema=TARGET_SCHEMA,
                con=connection,
                if_exists="append",
                index=False,
                chunksize=100,
                method="multi",
            )

            inquiry_df.to_sql(
                name="customer_inquiry",
                schema=TARGET_SCHEMA,
                con=connection,
                if_exists="append",
                index=False,
                chunksize=100,
                method="multi",
            )

        print(f"고객 적재: {len(customer_df)}건")
        print(f"기존 문의 적재: {len(inquiry_df)}건")

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
        SQLAlchemyError,
    ) as error:
        print("[초기 데이터 적재 오류]")
        print(error)
        sys.exit(1)

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
