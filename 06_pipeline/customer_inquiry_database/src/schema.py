from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import Engine



def build_metadata(schema_name: str) -> tuple[MetaData, dict[str, Table]]:
    #postgreSQL 테이블 정의

    metadata = MetaData(
        schema=schema_name,
    )

    execution_history = Table(
        'quality_execution_history',
        metadata,
        Column('execution_id', UUID(as_uuid=True), primary_key=True),
        Column('started_at', DateTime(timezone=True), nullable=False),
        Column('complete_at', DateTime(timezone=True)),
        Column('status', String(20), nullable=False),
        Column('source_file_name', Text, nullable=False),
        Column('raw_count', Integer, nullable=False, server_default='0'),
        Column('standardized_count', Integer, nullable=False, server_default='0'),
        Column('valid_count', Integer, nullable=False, server_default='0'),
        Column('invalid_count', Integer, nullable=False, server_default='0'),
        Column('issue_count', Integer, nullable=False, server_default='0'),
        Column('error_message', Text),
        Column('created_at', DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    )

    raw_table = Table(
        'customer_inquiry_raw',
        metadata,
        Column('load_id', BigInteger, primary_key=True, autoincrement=True),
        Column(
            'execution_id',
               UUID(as_uuid=True),
            ForeignKey(f"{schema_name}.quality_execution_history.execution_id",ondelete='CASCADE'),
            nullable=False),
        Column('source_row_number', Integer, nullable=False),
        Column('source_inquiry_id', Text),
        Column('author_name_raw', Text),
        Column('country_name_raw', Text),
        Column('language_code_raw', Text),
        Column('posted_at', Text),
        Column('inquiry_type_raw', Text),
        Column('priority_raw', Text),
        Column('product_code_raw', Text),
        Column('product_name_raw', Text),
        Column('answer_status_raw', Text),
        Column('inquiry_title_raw', Text),
        Column('inquiry_text_raw', Text),
        Column('source_url', Text),
        Column('collected_at', DateTime(timezone=True)),
        UniqueConstraint('execution_id', 'source_row_number', name='uq_raw_execution_row'),
    )

    def standardized_columns(
             include_quality: bool,
             unique_constraint_name: str
    )-> list[Column]:
        columns: list[Column] = [
            Column('load_id', BigInteger, primary_key=True, autoincrement=True),
            Column('execution_id',
                   UUID(as_uuid=True),
                   ForeignKey(f"{schema_name}.quality_execution_history.execution_id",ondelete='CASCADE'),
                   nullable=False
            ),
            Column('source_row_number', Integer, nullable=False),
            Column('source_inquiry_id', Text),
            Column('author_name_raw', Text),
            Column('author_name', Text),
            Column('country_name_raw', Text),
            Column('country_code', String(10)),
            Column('country_name', Text),
            Column('language_code_raw', Text),
            Column('language_code', String(20)),
            Column('default_language_code', String(20)),
            Column('posted_at_raw', Text),
            Column('posted_at', DateTime(timezone=True)),
            Column('inquiry_type_raw', Text),
            Column('inquiry_type_code', String(50)),
            Column('inquiry_type_name', Text),
            Column('priority_raw', Text),
            Column('priority_code', String(20)),
            Column('priority_level', Integer),
            Column('product_code_raw', Text),
            Column('product_code', String(30)),
            Column('product_name_raw', Text),
            Column('product_name', Text),
            Column('reference_product_name', Text),
            Column('product_category_code', String(50)),
            Column('answer_status_raw', Text),
            Column('answer_status_code', String(30)),
            Column('answer_status_name', Text),
            Column('inquiry_title_raw', Text),
            Column('inquiry_title', Text),
            Column('inquiry_text_raw', Text),
            Column('inquiry_text', Text),
            Column('source_url', Text),
            Column('collected_at', DateTime(timezone=True)),
            Column('standardized_at', DateTime(timezone=True)),
        ]

        if include_quality:
            columns.extend(
                [
                    Column('quality_status', String(20), nullable=False),
                    Column('quality_issue_count', Integer, nullable=False),
                ]
            )

        columns.append(
            UniqueConstraint('execution_id', 'source_row_number', name=unique_constraint_name)
        )

        return columns



    standardized_table = Table(
        'customer_inquiry_standardized',
        metadata,
        *standardized_columns(
            include_quality=False,
            unique_constraint_name='un_standardized_execution_row',
        )
    )

    valid_table = Table(
        'customer_inquiry_valid',
        metadata,
        *standardized_columns(
            include_quality=True,
            unique_constraint_name='un_valid_execution_row',
        )
    )

    invalid_table = Table(
        'customer_inquiry_invalid',
        metadata,
        *standardized_columns(
            include_quality=True,
            unique_constraint_name='un_invalid_execution_row',
        )
    )

    issue_table = Table(
        'customer_inquiry_quality_issue',
        metadata,
        Column('issue_id', BigInteger, primary_key=True, autoincrement=True),
        Column('execution_id',
               UUID(as_uuid=True),
               ForeignKey(f"{schema_name}.quality_execution_history.execution_id",ondelete='CASCADE'),nullable=False),
        Column('source_row_index', Integer, nullable=False),
        Column('source_inquiry_id', Text),
        Column('rule_code', String(100), nullable=False),
        Column('column_name', String(100), nullable=False),
        Column('invalid_value', Text),
        Column('error_message', Text, nullable=True)
    )

    Index('ix_raw_execution_id',
          raw_table.c.execution_id
          )

    Index('ix_raw_source_inquiry_id',
          raw_table.c.source_inquiry_id
    )

    Index('ix_standardize_execution_id',
          standardized_table.c.execution_id
    )

    Index('ix_valid_execution_id',
          valid_table.c.execution_id
    )

    Index('ix_invalid_execution_id',
          invalid_table.c.execution_id
    )

    Index('ix_issue_execution_id',
          issue_table.c.execution_id
    )

    Index('ix_issue_rule_code',
          issue_table.c.rule_code
    )

    return metadata, {
        'execution_history': execution_history,
        'raw': raw_table,
        'standardized': standardized_table,
        'valid': valid_table,
        'invalid': invalid_table,
        'issue': issue_table
    }





def create_schema_and_tables(
    engine: Engine,
    schema_name: str
)-> dict[str, Table]:
    #스키마와 테이블이 없으면 생성

    metadata, tables = build_metadata(schema_name)

    print(metadata)

    with engine.begin() as connection:
        connection.execute(
            text(
                f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'
            )
        )

    metadata.create_all(
        engine,
        checkfirst=True
    )

    return tables
