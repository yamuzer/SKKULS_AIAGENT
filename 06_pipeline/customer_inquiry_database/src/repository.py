from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pandas as pd
from sqlalchemy import func, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.sql.schema import Table

@dataclass(frozen=True)
class InputFiles:
    raw: Path
    standardized: Path
    valid: Path
    invalid: Path
    issue: Path


@dataclass(frozen=True)
class LoadedFrames:
    raw: pd.DataFrame
    standardized: pd.DataFrame
    valid: pd.DataFrame
    invalid: pd.DataFrame
    issue: pd.DataFrame


def read_csv(
        path: Path,
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f'입력 CSV가 없습니다. : {path}')

    return pd.read_csv(
        path,
        encoding='utf-8-sig',
        keep_default_na=False,
    )


def load_input_frames(
        files: InputFiles,
) -> LoadedFrames:

    return LoadedFrames(
        raw=read_csv(files.raw),
        standardized=read_csv(files.standardized),
        valid=read_csv(files.valid),
        invalid=read_csv(files.invalid),
        issue=read_csv(files.issue),
    )

def build_execution_id() -> UUID:
    return uuid4()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def insert_execution_start(
    engine: Engine,
    execution_table: Table,
    execution_id: UUID,
    source_file_name: str
) -> None:

    with engine.begin() as connection:
        connection.execute(
            execution_table.insert().values(),
            [
                {
                    'execution_id': execution_id,
                    'started_at': utc_now(),
                    'status': "RUNNING",
                    'source_file_name': source_file_name,
                }
            ]
        )


def prepare_dataframe(
    dataframe: pd.DataFrame,
    execution_id: UUID,
    add_row_number: bool
) -> pd.DataFrame:

    prepared_df = dataframe.copy()

    prepared_df.insert(
        0,
        'execution_id',
        execution_id,
    )

    if add_row_number:
        prepared_df.insert(
            1,
            'source_row_number',
            range(1, len(prepared_df)+1),
        )

    datetime_columns = [
        'posted_at',
        'collected_at',
        'standardized_at'
    ]

    for column in datetime_columns:
        if column in prepared_df.columns:
            prepared_df[column] = pd.to_datetime(prepared_df[column], errors='coerce', utc=True)

    integer_columns = [
        'priority_level',
        'quality_issue_count',
        'source_row_index'
    ]

    for column in integer_columns:
        if column in prepared_df.columns:
            prepared_df[column] = pd.to_numeric(prepared_df[column], errors='coerce').astype("Int64")

    return prepared_df


def normalize_scalar(
        value: Any
) -> Any:
    #pandas, numpy 값을 SQLAlchemy가 처리하기 쉬운 python value로 바꾸어줌

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

    return [
        {
            column: normalize_scalar(value) for column, value in row.items()
        }
        for row in dataframe.to_dict(orient='records')
    ]



def insert_records(
    connection,
    table: Table,
    dataframe: pd.DataFrame,
) -> None:

    records = dataframe_to_records(dataframe)

    if records:
        connection.execute(table.insert(), records)


def count_for_execution(
        connection,
        table: Table,
        execution_id: UUID
) -> int:
    statement = (
        select(
            func.count()
        )
        .select_from(
            table
        )
        .where(
            table.c.execution_id == execution_id
        )
    )

    return int(
        connection.scalar(statement) or 0
    )


def load_all_data(
    engine: Engine,
    tables: dict[str, Table],
    execution_id: UUID,
    frames: LoadedFrames,
) -> dict[str, int]:

    prepared = {
        'raw':
            prepare_dataframe(
                frames.raw,
                execution_id,
                add_row_number=True
        ),
        'standardized':
            prepare_dataframe(
                frames.standardized,
                execution_id,
                add_row_number=True
        ),
        'valid':
            prepare_dataframe(
                frames.valid,
                execution_id,
                add_row_number=True
        ),
        'invalid':
            prepare_dataframe(
                frames.invalid,
                execution_id,
                add_row_number=True
        ),
        'issue':
            prepare_dataframe(
                frames.issue,
                execution_id,
                add_row_number=False
            )
    }

    expected_counts = {
        name: len(dataframe) for name, dataframe in prepared.items()
    }

    with engine.begin() as connection:
        for name in ['raw', 'standardized', 'valid', 'invalid', 'issue']:
            insert_records(
                connection,
                tables[name],
                prepared[name],
            )

        actual_counts = {
            name: count_for_execution(connection, tables[name], execution_id) for name in expected_counts
        }

        if actual_counts != expected_counts:
            raise RuntimeError(f'적재 건수 검증에 실패했습니다. 예상:{expected_counts}, 실제:{actual_counts}')

        connection.execute(
            update(
                tables['execution_history']
            )
            .where(
                tables['execution_history'].c.execution_id == execution_id
            )
            .values(
                complete_at=utc_now(),
                status ='SUCCESS',
                raw_count=actual_counts['raw'],
                standardized_count=actual_counts['standardized'],
                valid_count=actual_counts['valid'],
                invalid_count=actual_counts['invalid'],
                issue_count=actual_counts['issue'],
                error_message=None
            )
        )

    return actual_counts