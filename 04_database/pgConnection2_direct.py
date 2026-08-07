# 한행, 여러행, 전부 가져오기

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

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

def print_title(title: str) -> None:
    print()
    print('='* 80)
    print(title)
    print('=' * 80)

# 결과에서 한 줄(row)만 가져옴, 한 줄만 필요한 경우
def print_employee_rows(rows: list[dict[str, Any]]) -> None:
        if not rows:
            print('조회된 직원이 없습니다.')
            return
        print(
            f'{"직원번호":<10}'
            f'{"직원이름":<12}'
            f'{"직원직무":<10}'
            f'{"직원급여":>15}'
        )
        for row in rows:
            print(f"{row['employee_id']:<10}"
                  f"{row['employee_name']:<12}"
                  f"{row['job_title']:<10}"
                  f"{row['salary']:>15}"
                  )


# 	결과에서 지정한 개수만큼 줄 가져옴, 데이터 양이 많을 때 적당히 나눠서 가져올 때
def run_fetchmany_example(cursor: psycopg.Cursor) -> None:
    print_title('fetch many example')
    cursor.execute('''
        SELECT
            employee_id,
            employee_name,
            job_title,
            salary
        FROM python_lab.employee
        ORDER BY
            salary DESC,
            employee_id
        LIMIT 10;
    ''')

    first_row = cursor.fetchmany(3)
    print_employee_rows(first_row)
    # 커서가 연속해서 다음 행을 조회함
    second_row = cursor.fetchmany(4)
    print_employee_rows(second_row)


# 남아있는 모든 줄(row)을 한번에 가져옴, 결과가 적을 때, 전부 가져올 때
def run_fetchall_example(cursor: psycopg.Cursor) -> None:
    print_title('fetch all example')
    cursor.execute('''
        SELECT
            d.department_id,
            d.department_name,
            d.location_name,
            COUNT(e.employee_id) AS employee_count,
            ROUND(AVG(e.salary), 0) AS average_salary
        FROM python_lab.department AS d
        LEFT JOIN python_lab.employee AS e
            ON d.department_id = e.department_id
        GROUP BY
            d.department_id, 
            d.department_name,
            d.location_name
        ORDER BY d.department_id;
    ''')
    rows = cursor.fetchall()
    print(
        f'{"부서번호":<10}'
        f'{"부서명":<16}'
        f'{"지역":<10}'
        f'{"직원 수":>10}'
        f'{"평균 급여":>15}'
    )
    print('='*80)
    for row in rows:
        average_salary = row['average_salary']
        average_salary_text = f"{int(average_salary):,}"
        print(f"{row['department_id']:<10}"
              f"{row['department_name']:<16}"
              f"{row['location_name']:<10}"
              f"{row['employee_count']:>10}"
              f"{average_salary_text:>18}"
              )

def test_database_connection() -> None:
    try:
        config = load_database_config()
        print(config)
        print('PostgreSQL 연결을 시작합니다.')

        with psycopg.connect(**config,
                             row_factory=dict_row
                             ) as connection:
            with connection.cursor() as cursor:
                run_fetchmany_example(cursor)
                run_fetchall_example(cursor)


    except FileNotFoundError as error:
        print(f'설정 파일 오류 : {error}')
        sys.exit(1)
    except ValueError as error:
        print(f'환경 변수 오류 : {error}')
        sys.exit(1)
    except psycopg.OperationalError as error:
        print(f'\nPostgreSQL 연결 오류 : {error}')
        sys.exit(1)
    except psycopg.errors.UnerfinedTableError as error:
        print(f'\n테이블 없음 오류 : {error}')
        sys.exit(1)
    except psycopg.errors as error:
        print(f'\nSQL 실행 오류 : {error}')
        sys.exit(1)





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
