from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pandas as pd
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    URL,
    create_engine,
    func,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine import Engine

from src.config_loader import DatabaseSettings
from src.models import ValidationResult


def create_postgresql_engine(settings: DatabaseSettings) -> Engine:
    url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.user,
        password=settings.password,
        host=settings.host,
        port=settings.port,
        database=settings.database,
    )
    return create_engine(
        url,
        echo=settings.echo_sql,
        pool_pre_ping=True,
    )


def build_metadata(schema: str) -> tuple[MetaData, dict[str, Table]]:
    metadata = MetaData(schema=schema)

    execution = Table(
        "pipeline_run_history",
        metadata,
        Column("execution_id", PG_UUID(as_uuid=True), primary_key=True),
        Column("started_at", DateTime(timezone=True), nullable=False),
        Column("completed_at", DateTime(timezone=True)),
        Column("status", String(20), nullable=False),
        Column("raw_count", Integer, nullable=False, server_default="0"),
        Column("standardized_count", Integer, nullable=False, server_default="0"),
        Column("valid_count", Integer, nullable=False, server_default="0"),
        Column("invalid_count", Integer, nullable=False, server_default="0"),
        Column("issue_count", Integer, nullable=False, server_default="0"),
        Column("error_message", Text),
    )

    raw = Table(
        "web_inquiry_raw",
        metadata,
        Column("load_id", BigInteger, primary_key=True, autoincrement=True),
        Column(
            "execution_id",
            PG_UUID(as_uuid=True),
            ForeignKey(f"{schema}.pipeline_run_history.execution_id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("source_row_number", Integer, nullable=False),
        Column("source_inquiry_id", Text),
        Column("author_name_raw", Text),
        Column("country_name_raw", Text),
        Column("language_code_raw", Text),
        Column("posted_at_raw", Text),
        Column("inquiry_type_raw", Text),
        Column("priority_raw", Text),
        Column("product_code_raw", Text),
        Column("product_name_raw", Text),
        Column("answer_status_raw", Text),
        Column("inquiry_title_raw", Text),
        Column("inquiry_text_raw", Text),
        Column("source_url", Text),
        Column("collected_at", DateTime(timezone=True)),
        UniqueConstraint(
            "execution_id",
            "source_row_number",
            name="uq_web_raw_run_row",
        ),
    )

    def business_columns(include_quality: bool, constraint_name: str) -> list:
        columns = [
            Column("load_id", BigInteger, primary_key=True, autoincrement=True),
            Column(
                "execution_id",
                PG_UUID(as_uuid=True),
                ForeignKey(
                    f"{schema}.pipeline_run_history.execution_id",
                    ondelete="CASCADE",
                ),
                nullable=False,
            ),
            Column("source_row_number", Integer, nullable=False),
            Column("source_inquiry_id", Text),
            Column("author_name", Text),
            Column("country_code", String(10)),
            Column("language_code", String(20)),
            Column("posted_at", DateTime(timezone=True)),
            Column("inquiry_type_code", String(50)),
            Column("priority_code", String(20)),
            Column("product_code", String(30)),
            Column("product_name", Text),
            Column("answer_status_code", String(30)),
            Column("inquiry_title", Text),
            Column("inquiry_text", Text),
            Column("source_url", Text),
            Column("collected_at", DateTime(timezone=True)),
            Column("standardized_at", DateTime(timezone=True)),
        ]
        if include_quality:
            columns.extend(
                [
                    Column("quality_status", String(20), nullable=False),
                    Column("quality_issue_count", Integer, nullable=False),
                ]
            )
        columns.append(
            UniqueConstraint(
                "execution_id",
                "source_row_number",
                name=constraint_name,
            )
        )
        return columns

    standardized = Table(
        "web_inquiry_standardized",
        metadata,
        *business_columns(False, "uq_web_standardized_run_row"),
    )
    valid = Table(
        "web_inquiry_valid",
        metadata,
        *business_columns(True, "uq_web_valid_run_row"),
    )
    invalid = Table(
        "web_inquiry_rejected",
        metadata,
        *business_columns(True, "uq_web_rejected_run_row"),
    )
    issue = Table(
        "web_inquiry_quality_issue",
        metadata,
        Column("issue_id", BigInteger, primary_key=True, autoincrement=True),
        Column(
            "execution_id",
            PG_UUID(as_uuid=True),
            ForeignKey(f"{schema}.pipeline_run_history.execution_id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("source_row_number", Integer, nullable=False),
        Column("source_inquiry_id", Text),
        Column("rule_code", String(100), nullable=False),
        Column("column_name", String(100), nullable=False),
        Column("invalid_value", Text),
        Column("error_message", Text, nullable=False),
    )

    return metadata, {
        "execution": execution,
        "raw": raw,
        "standardized": standardized,
        "valid": valid,
        "invalid": invalid,
        "issue": issue,
    }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _normalize(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass
    return value


def _records(
    dataframe: pd.DataFrame,
    execution_id: UUID,
    columns: list[str],
) -> list[dict[str, Any]]:
    rows = []
    for row in dataframe.to_dict(orient="records"):
        record = {"execution_id": execution_id}
        for column in columns:
            record[column] = _normalize(row.get(column))
        rows.append(record)
    return rows


def _count(connection, table: Table, execution_id: UUID) -> int:
    return int(
        connection.scalar(
            select(func.count())
            .select_from(table)
            .where(table.c.execution_id == execution_id)
        )
        or 0
    )


def load_to_postgresql(
    raw_df: pd.DataFrame,
    standardized_df: pd.DataFrame,
    validation: ValidationResult,
    settings: DatabaseSettings,
) -> dict[str, Any]:
    engine = create_postgresql_engine(settings)
    metadata, tables = build_metadata(settings.schema)
    execution_id = uuid4()

    raw_prepared = raw_df.copy()
    raw_prepared.insert(0, "source_row_number", range(1, len(raw_prepared) + 1))

    for dataframe in [
        raw_prepared,
        standardized_df,
        validation.valid_df,
        validation.invalid_df,
    ]:
        for column in ["posted_at", "collected_at", "standardized_at"]:
            if column in dataframe.columns:
                dataframe[column] = pd.to_datetime(
                    dataframe[column],
                    errors="coerce",
                    utc=True,
                )

    raw_columns = [
        "source_row_number",
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
        "collected_at",
    ]
    standard_columns = [
        "source_row_number",
        "source_inquiry_id",
        "author_name",
        "country_code",
        "language_code",
        "posted_at",
        "inquiry_type_code",
        "priority_code",
        "product_code",
        "product_name",
        "answer_status_code",
        "inquiry_title",
        "inquiry_text",
        "source_url",
        "collected_at",
        "standardized_at",
    ]
    quality_columns = standard_columns + ["quality_status", "quality_issue_count"]
    issue_columns = [
        "source_row_number",
        "source_inquiry_id",
        "rule_code",
        "column_name",
        "invalid_value",
        "error_message",
    ]

    frames = {
        "raw": (raw_prepared, raw_columns),
        "standardized": (standardized_df, standard_columns),
        "valid": (validation.valid_df, quality_columns),
        "invalid": (validation.invalid_df, quality_columns),
        "issue": (validation.issue_detail_df, issue_columns),
    }
    expected = {name: len(frame) for name, (frame, _) in frames.items()}

    try:
        with engine.begin() as connection:
            connection.execute(
                text(f'CREATE SCHEMA IF NOT EXISTS "{settings.schema}"')
            )
        metadata.create_all(engine, checkfirst=True)

        with engine.begin() as connection:
            connection.execute(
                tables["execution"].insert(),
                [{"execution_id": execution_id, "started_at": _utc_now(), "status": "RUNNING"}],
            )

        with engine.begin() as connection:
            for name, (frame, columns) in frames.items():
                records = _records(frame, execution_id, columns)
                if records:
                    connection.execute(tables[name].insert(), records)

            actual = {
                name: _count(connection, tables[name], execution_id)
                for name in expected
            }
            if actual != expected:
                raise RuntimeError(f"적재 건수 불일치: 예상={expected}, 실제={actual}")

            connection.execute(
                update(tables["execution"])
                .where(tables["execution"].c.execution_id == execution_id)
                .values(
                    completed_at=_utc_now(),
                    status="SUCCESS",
                    raw_count=actual["raw"],
                    standardized_count=actual["standardized"],
                    valid_count=actual["valid"],
                    invalid_count=actual["invalid"],
                    issue_count=actual["issue"],
                    error_message=None,
                )
            )

        return {
            "execution_id": str(execution_id),
            "database": settings.database,
            "schema": settings.schema,
            "status": "SUCCESS",
            "loaded_counts": actual,
        }

    except Exception as error:
        try:
            with engine.begin() as connection:
                connection.execute(
                    update(tables["execution"])
                    .where(tables["execution"].c.execution_id == execution_id)
                    .values(
                        completed_at=_utc_now(),
                        status="FAILED",
                        error_message=str(error)[:4000],
                    )
                )
        except Exception:
            pass
        raise
    finally:
        engine.dispose()
