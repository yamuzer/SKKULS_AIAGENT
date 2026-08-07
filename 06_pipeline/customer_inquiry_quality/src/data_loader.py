from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pandas as pd

def load_raw_data(csv_path: Path) -> pd.DataFrame:

    if not csv_path.exists():
        raise FileNotFoundError(f'원천 CSV가 없습니다. : {csv_path}')

    raw_df = pd.read_csv(
        csv_path,
        encoding='utf-8-sig',
        dtype="string",
        keep_default_na=False,
    )

    if raw_df.empty:
        raise ValueError('원천 CSV에 데이터가 없습니다.')

    return raw_df


def load_reference_data(reference_dir: Path) -> dict[str, pd.DataFrame]:

    reference_files = {
        'country': 'country_reference.csv',
        'product': 'product_reference.csv',
        'inquiry_type': 'inquiry_type_reference.csv',
        'priority': 'priority_reference.csv',
        'answer_status': 'answer_status_reference.csv'
    }

    references = {}

    for name, file_name in reference_files.items():
        path = reference_dir / file_name

        if not path.exists():
            raise FileNotFoundError(f'기준 정보 파일이 없습니다. : {path}')

        references[name] = pd.read_csv(
            path,
            encoding='utf-8-sig',
            dtype='string',
            keep_default_na=False,
        )

    return references


def load_quality_rules(json_path: Path) -> dict[str, Any]:
    if not json_path.exists():
        raise FileNotFoundError(f'품질 규칙 파일이 없습니다. : {json_path}')

    return json.loads(json_path.read_text(encoding='utf-8'))























