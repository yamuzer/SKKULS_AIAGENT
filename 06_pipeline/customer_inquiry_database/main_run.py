from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.repository import (
    InputFiles,
    load_input_frames,
    build_execution_id,
    insert_execution_start,
    load_all_data
)

from src.database import (
    load_database_settings,
    create_postgresql_engine
)

from src.schema import (
    create_schema_and_tables
)


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / "config"  / ".env"

INPUT_FILES = InputFiles(
    raw=(
        BASE_DIR / "data" / "raw" / "customer_inquiry_raw.csv"
    ),
    standardized=(
        BASE_DIR / "data" / "standardized" / "customer_inquiry_standardized.csv"
    ),
    valid=(
        BASE_DIR / "data" / "quality" / "customer_inquiry_valid.csv"
    ),
    invalid=(
            BASE_DIR / "data" / "quality" / "customer_inquiry_invalid.csv"
    ),
    issue=(
        BASE_DIR / "data" / "quality" / "quality_issue_detail.csv"
    )
)

LOAD_PLAN_PATH = BASE_DIR / "reports" / "database_load_plan.json"

LOAD_SUMMARY_PATH = BASE_DIR / "reports" / "database_load_summary.json"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="품질 데이터를 PostgreSQL에 적재합니다."
    )

    parser.add_argument(
        '--check-only',
        action='store_true',
        help='PostgreSQL에 연결하지 않고 입력 파일과 적재 건수만 검사합니다.'
    )

    return parser.parse_args()


def print_title(title: str) -> None:
    print()
    print('=' * 100)
    print(title)
    print('=' * 100)


def create_load_plan(
    frames,
    database_name: str,
    schema_name: str,
) -> dict:
    return {
        'database': database_name,
        'schema': schema_name,
        'tables':{
            'customer_inquiry_raw': len(frames.raw),
            'customer_inquiry_standardized': len(frames.standardized),
            'customer_inquiry_valid': len(frames.valid),
            'customer_inquiry_invalid': len(frames.invalid),
            'customer_inquiry_quality_issue': len(frames.issue),
        }
    }


def main() -> None:
    arguments = parse_arguments()

    print_title('1. 결과 CSV 읽기')

    frames = load_input_frames(
        INPUT_FILES
    )

    #print(frames)

    settings = load_database_settings(
        env_path=ENV_PATH,
        require_password=(not arguments.check_only)
    )
    #print(settings)

    load_plan = create_load_plan(
        frames=frames,
        database_name=settings.database,
        schema_name=settings.schema,
    )

    #print(load_plan)

    LOAD_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)

    LOAD_PLAN_PATH.write_text(
        json.dumps(
            load_plan,
            ensure_ascii=False,
            indent=2
        ),
        encoding='utf-8'
    )

    if arguments.check_only:
        print('\n입력 파일 검사와 적재 계획 생성을 완료했습니다.')
        print(f'적재 계획: {LOAD_PLAN_PATH}')
        return

    print_title('2. postgreSQL engine 생성')
    engine = create_postgresql_engine(settings)
    #print(engine)

    execution_id = build_execution_id()

    #print(execution_id)
    try:
        print_title('3. 스키마, 테이블 생성')
        tables = create_schema_and_tables(
            engine=engine,
            schema_name=settings.schema,
        )

        print_title('4. 실행 이력 등록')
        insert_execution_start(
            engine=engine,
            execution_table=tables['execution_history'],
            execution_id=execution_id,
            source_file_name=INPUT_FILES.raw.name
        )

        print_title('5. 품질 데이터 일괄 적재')
        counts = load_all_data(
            engine=engine,
            tables=tables,
            execution_id=execution_id,
            frames=frames,
        )

        print(f'load data: {counts}')



    except Exception as e:
        print(e)
    finally:
        engine.dispose()






if __name__ == "__main__":
    main()
