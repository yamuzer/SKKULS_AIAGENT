# 연결하기

from __future__ import annotations

import os
import sys
from pathlib import Path

# pip install psycopg psycopg-binary dotenv
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR)
ENV_PATH = BASE_DIR / ".env"

def load_database_config() -> dict[str, str | int]:
    if not ENV_PATH.exists():
        raise FileNotFoundError('.env 파일이 없습니다.')
    load_dotenv(dotenv_path=ENV_PATH)
    required_keys = [
        'DB_HOST',
        'DB_PORT',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    if missing_keys:
        missing_text = ", ".join(missing_keys)
        raise ValueError(
            f'.env파일에 다음 설정이 없습니다.: {missing_text}'
        )
    return {
        'host': os.environ["DB_HOST"],
        'port': int(os.environ["DB_PORT"]),
        'dbname': os.environ["DB_NAME"],
        'user': os.environ["DB_USER"],
        'password': os.environ["DB_PASSWORD"],
        'connect_timeout': 5
    }

def test_database_connection() -> None:
    config = load_database_config()
    print(config)
    print('PostgreSQL 연결을 시작합니다.')

    with psycopg.connect(**config,
                         row_factory=dict_row
                         ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                           '''
                           SELECT
                                current_database() AS database_name,
                                current_user AS login_user,
                                current_schema() AS current_schema,
                                version() AS postgresql_version
                           '''
                           )
            connection_info = cursor.fetchone()
            print(connection_info)

            cursor.execute(
                            """
                 SELECT
                    (SELECT COUNT(*)
                    FROM python_lab.department) AS department_count,
                    (SELECT COUNT(*)
                    FROM python_lab.department) AS employee_count;
                            """
            )
            data_info = cursor.fetchone()
            print('\n[실습 데이터 확인]')
            print(f'부서 수: {data_info["department_count"]} 건')
            print(f'직원 수: {data_info["employee_count"]} 명')



def main() -> None:
    try:
        test_database_connection()
    except FileNotFoundError as error :
        print(f'설정 파일 오류 : {error}')
        sys.exit(1)
    except ValueError as error :
        print(f'환경 변수 오류 : {error}')
        sys.exit(1)
    except psycopg.OperationalError as error :
        print(f'\nPostgreSQL 연결 실패 : {error}')
        sys.exit(1)
    except psycopg.errors as error :
        print(f'\nSQL 실행 오류 : {error}')
        sys.exit(1)





if __name__ == "__main__":
    main()
