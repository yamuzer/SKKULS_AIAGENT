from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv


SCHEMA_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str
    schema: str
    echo_sql: bool


def load_raw_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"원천 CSV가 없습니다: {path}")
    dataframe = pd.read_csv(
        path,
        encoding="utf-8-sig",
        dtype="string",
        keep_default_na=False,
    )
    if dataframe.empty:
        raise ValueError("원천 CSV가 비어 있습니다.")
    return dataframe


def load_reference_data(reference_dir: Path) -> dict[str, pd.DataFrame]:
    files = {
        "country": "country_reference.csv",
        "product": "product_reference.csv",
        "inquiry_type": "inquiry_type_reference.csv",
        "priority": "priority_reference.csv",
        "answer_status": "answer_status_reference.csv",
    }
    references = {}
    for name, filename in files.items():
        path = reference_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"기준정보가 없습니다: {path}")
        references[name] = pd.read_csv(
            path,
            encoding="utf-8-sig",
            dtype="string",
            keep_default_na=False,
        )
    return references


def load_quality_rules(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"품질 규칙이 없습니다: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_database_settings(env_path: Path) -> DatabaseSettings:
    load_dotenv(dotenv_path=env_path, override=False)
    settings = DatabaseSettings(
        host=os.getenv("PGHOST", "127.0.0.1"),
        port=int(os.getenv("PGPORT", "5432")),
        database=os.getenv("PGDATABASE", "customer_quality_practice"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", ""),
        schema=os.getenv("PGSCHEMA", "web_inquiry_quality"),
        echo_sql=os.getenv("SQLALCHEMY_ECHO", "false").strip().lower()
        in {"1", "true", "yes", "y"},
    )
    if not settings.password:
        raise ValueError("config/.env의 PGPASSWORD를 입력하세요.")
    if not SCHEMA_PATTERN.fullmatch(settings.schema):
        raise ValueError("PGSCHEMA 형식이 올바르지 않습니다.")
    return settings
