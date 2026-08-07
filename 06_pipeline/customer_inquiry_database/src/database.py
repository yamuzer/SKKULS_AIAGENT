from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.engine import Engine

SCHEMA_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z_0-9]*$")

@dataclass
class DatabaseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str
    schema: str
    echo_sql: bool


def load_database_settings(
    env_path: Path,
    require_password: bool = True
) -> DatabaseSettings:

    load_dotenv(
        dotenv_path=env_path,
        override=False
    )

    settings = DatabaseSettings(
        host=os.getenv('PGHOST', '127.0.0.1'),
        port=int(os.getenv('PGPORT', '5432')),
        database=os.getenv('PGDATABASE', 'global_customer_support'),
        user=os.getenv('PGUSER', 'postgres'),
        password=os.getenv('PGPASSWORD', ''),
        schema=os.getenv('PGSCHEMA', 'customer_quality'),
        echo_sql=(
            os.getenv('PGSQLECHOSQL', 'false')
            .strip()
            .lower() in {'1', 'true', 'yes', 'y'}
        )
    )

    if not SCHEMA_PATTERN.fullmatch(settings.schema):
        raise ValueError("PGSCHEMA가 영문자 또는 밑줄로 시작하고, 영문자 숫자 밑줄만 사용할 수 있습니다.")

    if require_password and not settings.password:
        raise ValueError('PASSWORD를 넣어주세요.')

    return settings


def create_postgresql_url(settings:DatabaseSettings) -> URL:
    '''
    비밀번호 특수문자도 안전하게 처리하는 postgresql URL 생성
    '''

    return URL.create(
        drivername='postgresql+psycopg',
        username=settings.user,
        password=settings.password,
        host=settings.host,
        port=settings.port,
        database=settings.database
    )


def create_postgresql_engine(settings: DatabaseSettings) -> Engine:

    return create_engine(
        create_postgresql_url(settings),
        echo=settings.echo_sql,
        pool_pre_ping=True
    )