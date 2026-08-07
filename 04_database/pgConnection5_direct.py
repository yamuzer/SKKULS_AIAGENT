# 데이터베이스 데이터를 업데이트 및 삭제하기
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
ENV_PATH = BASE_DIR / '.env'

ALLOWED_GRADES = {
    'BASIC',
    'SILVER',
    'GOLD'
}


def load_database_config() -> dict[str, str | int]:
    if not ENV_PATH.exists():
        raise FileNotFoundError('.env 파일이 없습니다.')

    load_dotenv(ENV_PATH)

    required_keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]

    missing_keys = [
        key for key in required_keys if not os.getenv(key)
    ]

    if missing_keys:
        missing_text = ", ".join(missing_keys)
        raise ValueError(
            f'.env파일에 다음 설정이 없습니다: {missing_text}'
        )

    return {
        'host': os.environ["DB_HOST"],
        'port': int(os.environ["DB_PORT"]),
        'dbname': os.environ["DB_NAME"],
        'user': os.environ["DB_USER"],
        'password': os.environ["DB_PASSWORD"],
        'connect_timeout': 5
    }

def read_required_text(message: str) -> str:
    while True:
        value = input(message).strip()

        if value:
            return value
        print('필수 입력값입니다. 다시 입력하세요.')


def read_customer_grade() -> str:
    while True:
        grade = input(
            '고객 등급을 입력하세요 '
            '(BASIC/SILVER/GOLD) '
            '[기본값: BASIC]: '
        ).strip().upper()

        if grade == '':
            return 'BASIC'
        if grade in ALLOWED_GRADES:
            return grade
        print('허용된 등급은 BASIC, SILVER, GOLD입니다.')

def read_joined_at() -> date:
    '''
    YYYY-MM-DD 형식
    '''

    while True:
        raw_value = input(
            '가입일을 입력하세요 '
            '(YYYY-MM-DD) '
            '[기본값: 오늘]: '
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
            '활성 고객입니까? (Y/N) [기본값: Y]: '
        ).strip().upper()

        if raw_value in {'', 'Y', 'YES'}:
            return True

        if raw_value in {'N', 'NO'}:
            return False

        print('Y 또는 N을 입력하세요.')


def get_customer_count(cursor: psycopg.Cursor) -> int:
    cursor.execute('''
                   SELECT COUNT(*) AS customer_count 
                   FROM python_lab.customer
                   ''')
    row = cursor.fetchone()
    return row['customer_count']


def print_title(title: str) -> None:
    print()
    print('=' * 80)
    print(title)
    print('=' * 80)


def print_employee_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print('조회된 직원이 없습니다.')
        return

    print()
    print(
        f"{'직원번호':<10}"
        f"{'직원이름':<12}"
        f"{'직무':<20}"
        f"{'급여':>15}"
    )
    print('-' * 80)
    for row in rows:
        print(
            f"{row['employee_id']:<10}"
            f"{row['employee_name']:<12}"
            f"{row['job_title']:<20}"
            f"{row['salary']:>15,}"
            )

def run_fetchmany_example(cursor: psycopg.Cursor) -> None:
    print_title('fetch many example')

    cursor.execute(
        """
        SELECT
            employee_id,
            employee_name,
            job_title,
            salary
        FROM python_lab.employee
        ORDER BY
            salary DESC,
            employee_id
        LIMIT 10 
        """
    )

    first_row = cursor.fetchmany(3)
    print_employee_rows(first_row)

    second_row = cursor.fetchmany(4)
    print_employee_rows(second_row)


def run_fetchall_example(cursor: psycopg.Cursor) -> None:
    print_title('fetch many example')

    cursor.execute(
        """
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
        ORDER BY d.department_id
        """
    )

    rows = cursor.fetchall()

    print(
        f"{'부서번호':<10}"
        f"{'부서명':<16}"
        f"{'지역':<10}"
        f"{'직원 수':>10}"
        f"{'평균 급여':>18}"
    )
    print('-' * 80)
    for row in rows:
        average_salary = row['average_salary']
        average_salary_text = f"{int(average_salary):,}"
        print(
            f"{row['department_id']:<10}"
            f"{row['department_name']:<16}"
            f"{row['location_name']:<10}"
            f"{row['employee_count']:>10}"
            f"{average_salary_text:>18}"
        )


def read_integer(
        message: str,
        default_value: int
) -> int:

    raw_value = input(f'{message} [기본값: {default_value}]: ').strip()

    if raw_value == '':
        return default_value

    try:
        return int(raw_value)
    except ValueError:
        print('정수가 아니므로 기본 값을 사용합니다.')
        return default_value



def search_by_minimum_salary(cursor:psycopg.Cursor) -> None:
    print_title('search by minimum salary')

    minimum_salary = read_integer(
        message='최소 급여를 입력해주세요',
        default_value=5000000
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
        """,
        (minimum_salary,)
    )

    rows = cursor.fetchall()
    print(
        f"급여 {minimum_salary}원 이상"
        f"직원 {len(rows)}"
    )


def search_by_name_keyword(cursor: psycopg.Cursor) -> None:
    print_title('search by name keyword')

    keyword = input('이름에 포함될 글자를 입력하세요 [기본값: 김]: ').strip()

    if keyword == '':
        keyword = "김"

    pattern = f"%{keyword}%"

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
        """,
        (pattern,)
    )

    rows = cursor.fetchall()

    print(f"이름에 '{keyword}'가 포함된 직원: {len(rows)}명")


def insert_customer(
    cursor: psycopg.Cursor,
    customer_name: str,
    country_name: str,
    email: str,
    customer_grade: str,
    joined_at: date,
    is_active: bool
) -> dict[str, Any]:

    cursor.execute(
        """
        INSERT INTO python_lab.customer(
            customer_name,
            country_name,
            email,
            customer_grade,
            joined_at,
            is_active
        )
        VALUES(
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        RETURNING
            customer_id,
            customer_name,
            country_name,
            email,
            customer_grade,
            joined_at,
            is_active,
            created_at
        """,
        (
            customer_name,
            country_name,
            email,
            customer_grade,
            joined_at,
            is_active
        )
    )

    inserted_row = cursor.fetchone()

    if inserted_row is None:
        raise RuntimeError('INSERT는 실행됐지만 반환된 행이 없습니다.')

    return inserted_row


def find_customer_by_id(
        cursor: psycopg.Cursor,
        customer_id: int
) -> dict[str, Any] | None:

    cursor.execute(
        """
        SELECT
            customer_id,
            customer_name,
            country_name,
            email,
            customer_grade,
            joined_at,
            is_active,
            created_at
        FROM python_lab.customer 
        WHERE customer_id = %s
        """,
        (customer_id,)
    )

    return cursor.fetchone()


def print_customer(
        customer: dict[str, Any] | None
) -> None:
    if customer is None:
        print('고객을 찾을 수 없습니다.')
        return

    print_title('customer details')
    print(f'고객 번호 : {customer["customer_id"]}')
    print(f'고객명 : {customer["customer_name"]}')
    print(f'국가 : {customer["country_name"]}')
    print(f'이메일 : {customer["email"]}')
    print(f'고객 등급 : {customer["customer_grade"]}')
    print(f'가입일 : {customer["joined_at"]}')
    print(f'활성여부 : {customer["is_active"]}')
    print(f'생성시각 : {customer["created_at"]}')
    print('=' * 80)


def update_customer(
    connection: psycopg.Connection,
    cursor: psycopg.Cursor
) -> None:
    print_title('update_customer')

    customer_id = read_integer('수정할 고객 번호를 입력하세요: ', 10)

    current_customer = find_customer_by_id(cursor, customer_id)

    if current_customer is None:
        print('해당 고객번호가 없습니다.')
        return

    print('\n[수정 전]')
    print_customer(current_customer)

    grade = input('새 고객 등급(BASIC/SILVER/GOLD): ').strip().upper()
    if grade not in ALLOWED_GRADES:
        print('허용되지 않는 등급입니다.')
        return

    active_text = input('활성 여부(Y/N): ').strip().upper()
    if active_text == "Y":
        is_active = True
    elif active_text == "N":
        is_active = False
    else:
        print('Y 또는 N을 입력하세요.')
        return

    cursor.execute('''
    UPDATE python_lab.customer 
    SET
        customer_grade = %s,
        is_active = %s
    WHERE customer_id = %s
    RETURNING
        customer_id,
        customer_name,
        country_name,
        email,
        customer_grade,
        joined_at,
        is_active,
        created_at
    ''',(grade, is_active, customer_id))

    updated_customer = cursor.fetchone()
    affected_count = cursor.rowcount # 수정된 행의 수
    connection.commit()

    print(f'\n수정된 행 수: {affected_count} 행')
    print('\n[수정 후]')
    print_customer(updated_customer)


def delete_customer_demo(
        connection: psycopg.Connection,
        cursor: psycopg.Cursor) -> None:
    print_title('delete_customer_demo')
    customer_id = read_integer(
        '삭제할 고객 번호를 입력하세요.',
        '10'
    )
    customer = find_customer_by_id(cursor,
                                   customer_id)
    if customer is None:
        print('해당 고객은 없습니다.')
        return
    print('\n[삭제 대상]')
    print_customer(customer)

    confirm = input('삭제 SQL을 실행하시겠습니까? (Y/N): ').strip().upper()
    if confirm != 'Y':
        print('삭제를 취소했습니다.')
        return

    cursor.execute('''
    DELETE FROM python_lab.customer
    Where customer_id = %s
    RETURNING
        customer_id,
        customer_name,
        country_name,
        email,
        customer_grade,
        joined_at,
        is_active,
        created_at
    ''', (customer_id,)
    )

    delete_customer = cursor.fetchone()
    affected_count = cursor.rowcount
    print(f'DELETE 처리 후 행 수: {affected_count}')
    print('\n[DELETE가 실행된 고객]')
    print_customer(delete_customer)

    final_confirm = input('삭제를 반영하려면 COMMIT을 입력하세요. 그 외 입력은 ROLLBACK합니다.: ').strip().upper()
    if final_confirm == 'COMMIT':
        connection.commit()
        print('데이터베이스에 삭제가 반영되었습니다.')
    else:
        connection.rollback()
        print('ROLLBAC되어 삭제가 취소 되었습니다.')

        restore_customer = find_customer_by_id(cursor,customer_id)
        print('\n[ROLLBACK 후 복구 확인]')
        print_customer(restore_customer)




def main() -> None:
    try:
        config = load_database_config()
        print('PostgreSQL 연결을 시작합니다.')

        with psycopg.connect(
                **config,
                row_factory=dict_row
        ) as connection:
            with connection.cursor() as cursor:
                # update_customer(
                #     connection=connection,
                #     cursor=cursor
                # )
                delete_customer_demo(
                    connection=connection,
                    cursor=cursor
                )


    except FileNotFoundError as error:
        print(f'[설정 파일 오류]: {error}')
        sys.exit(1)

    except ValueError as error:
        print(f'[환경 변수 오류]: {error}')
        sys.exit(1)

    except psycopg.OperationalError as error:
        print(f'[PostgreSQL 연결 오류]: {error}')
        sys.exit(1)

    except psycopg.errors.UndefinedTable as error:
        print(f'[테이블 없음]: {error}')
        sys.exit(1)

    except psycopg.Error as error:
        print(f'[PostgreSQL SQL 오류]: {error}')
        sys.exit(1)

if __name__ == "__main__":
    main()