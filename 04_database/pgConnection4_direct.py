# 데이터베이스에 데이터 추가하기

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from datetime import date

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR)
ENV_PATH = BASE_DIR / ".env"

ALLOWED_GRADES = {
    'BASIC', 'SILVER', 'GOLD'
}


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


def read_required_text(message:str) -> str:
    while True:
        value = input(message).strip()
        if value:
            return value
        print('필수 입력값입니다. 다시 입력하세요.')


def read_customer_grade() -> str:
    while True:
        grade = input(
            '고객 등급을 입력하세요.'
            '(BASIC/SILVER/GOLD)'
            '[기본값:BASIC]: '
        ).strip().upper()

        if grade == '':
            return 'BASIC'
        if grade in ALLOWED_GRADES:
            return grade
        print('허용된 등급은 BASIC, SLIVER, GOLD 입니다.')

def read_joined_at() -> date:
    '''
    YYYY-MM-DD 형식
    '''
    while True:
        raw_value = input(
            '가입일을 입력하세요.'
            '(YYYY-MM-DD)'
            '[기본값:오늘]: '
        ).strip()

        if raw_value == '':
            return date.today()
        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            print('날짜 형식이 올바르지 않습니다. 예: 2026-07-30')

def read_active_value() -> bool:
    while True:
        raw_value = input(
            '활성 고객입니까? (Y/N) [기본값:Y]: '
        ).strip().upper()
        if raw_value in {'', 'Y', 'YES'}:
            return True
        if raw_value in {'N', 'NO'}:
            return False
        print('Y 또는 N을 입력하세요.')

def get_customer_count(cursor: psycopg.Cursor) -> int:
    cursor.execute("""
                   SELECT 
                       COUNT(*) AS customer_count 
                   FROM python_lab.customer
    """)
    row = cursor.fetchone()
    return row['customer_count']




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

def read_integer(message= str, default_value= int) -> int:
    raw_value = input(f'{message} [기본값: {default_value}]: ' ).strip()
    if raw_value =='':
        return default_value

    try:
        return int(raw_value)
    except ValueError:
        print('정수가 아니므로 기본 값을 사용합니다.')
        return default_value

def search_by_minimum_salary(cursor: psycopg.Cursor) -> None:
    print_title('search by minimum salary')
    minimum_salary = read_integer(
        message="최소 급여를 입력해주세요.",
        default_value = 5000000
    )

    cursor.execute(
        """
        SELECT
            employee_id, 
            employee_name,
            department_id,
            job_title,
            salary,
            employment_status
        FROM python_lab.employee
        WHERE salary >= %s
        ORDER BY 
            salary DESC,
            employee_id
        LIMIT 20
        """, (minimum_salary,)
    )

    rows = cursor.fetchall()
    print(
        f"급여 {minimum_salary}원 이상"
        f"직원 {len(rows)}"
    )

def search_by_name_keyword(cursor:psycopg.Cursor)->None:
    print_title('search by name keyword')
    keyword = input('이름에 포함된 글자를 입력하세요[기본값: 김 ]: ').strip()
    if keyword == '':
        keyword = "김"
    pattern = f'%{keyword}%'
    cursor.execute(
        """
        SELECT
            employee_id,
            employee_name,
            department_id,
            job_title,
            salary,
            employment_status
        FROM python_lab.employee
        WHERE employee_name LIKE %s
        ORDER BY employee_id
        LIMIT 30
        """, (pattern, )
    )
    rows = cursor.fetchall()
    print(
        f"이름에 {keyword}가 포함된 직원 {len(rows)}명"
    )

def insert_customer(
    cursor: psycopg.Cursor,
    customer_name: str,
    country_name: str,
    email:str,
    customer_grade:str,
    joined_at:date,
    is_active:bool
) -> dict[str, Any]:

    cursor.execute('''
    INSERT INTO python_lab.customer(
        customer_name,
        country_name,
        email,
        customer_grade,
        joined_at,
        is_active
    )
    VALUES(%s,%s,%s,%s,%s,%s)
    RETURNING
        customer_id,
        customer_name,
        email,
        customer_grade,
        joined_at,
        is_active
        create_at
    ''', (customer_name, country_name, email, customer_grade, joined_at, is_active)
                   )
    inserted_row = cursor.fetchone()

    if inserted_row is None:
        raise RuntimeError('insert는 실행됐지만 반환된 행이 없습니다.')

    return inserted_row



def main() -> None:
    try:
        config = load_database_config()
        print('PostgreSQL 연결을 시작합니다.')
        customer_name = read_required_text('고객명을 입력하세요 : ')
        country_name = read_required_text('국가명을 입력하세요. : ')
        email = read_required_text('이메일을 입력하세요. : ').lower()

        customer_grade = read_customer_grade()
        joined_at = read_joined_at()
        is_active = read_active_value()

        with psycopg.connect(**config,
                             row_factory=dict_row
                             ) as connection:
            with connection.cursor() as cursor:
                before_count = get_customer_count(cursor)

                inserted_customer = insert_customer(
                    cursor=cursor,
                    customer_name = customer_name,
                    country_name = country_name,
                    email = email,
                    customer_grade = customer_grade,
                    joined_at = joined_at,
                    is_active = is_active
                )

                connection.commit()
                after_count = get_customer_count(cursor)

        print('\n[고객 수 확인]')
        print(f'등록 전 고객 수: {before_count}')
        print(f'등록 후 고객 수: {after_count}')




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
