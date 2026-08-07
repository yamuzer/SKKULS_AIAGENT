# 데이터베이스 조회 및 데이터프레임으로 변환하여 csv 저장

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from datetime import date
import pandas as pd
import psycopg
from numpy.ma.core import minimum
from psycopg.rows import dict_row
from dotenv import load_dotenv
from sqlalchemy import Engine, URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'
OUTPUT_DIR = BASE_DIR / 'output'


def load_database_config() -> dict[str, Any]:
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
        'database': os.environ["DB_NAME"],
        'username': os.environ["DB_USER"],
        'password': os.environ["DB_PASSWORD"]
    }

def create_database_engine(config: dict[str, Any]) -> Engine:
    database_url = URL.create(
        drivername='postgresql+psycopg',
        username=config['username'],
        password=config['password'],
        host=config['host'],
        port=config['port'],
        database=config['database']
    )
    return  create_engine(database_url, pool_pre_ping=True)

def print_section(title: str) -> None:
    print()
    print('=' * 80)
    print(title)
    print('=' * 80)

def load_customer_dataframe(engine: Engine) -> pd.DataFrame:
    query = text(
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
        ORDER BY customer_id
        """
    )
    with engine.connect() as connection:
        customer_df = pd.read_sql_query(sql=query,
                                        con=connection,
                                        parse_dates=[
                                            'joined_at', 'created_at'
                                        ])
    return customer_df




def load_employee_join_dataframe(engine: Engine) -> pd.DataFrame:
    query = text(
        """
        SELECT
            e.employee_id,
            e.employee_name,
            e.job_title,
            e.salary,
            e.hire_date,
            e.employment_status,
            e.country_name,
            COALESCE(d.department_name, '부서 미배정') AS department_name,
            COALESCE(d.location_name, '미배정') AS location_name
        FROM python_lab.employee AS e 
        LEFT JOIN python_lab.department AS d 
            ON e.department_id = d.department_id
        ORDER BY e.department_id
            
        """
    )
    with engine.connect() as connection:
        employee_df = pd.read_sql_query(sql=query,
                                        con=connection,
                                        parse_dates=['hire_date'])
        return employee_df


def load_filtered_empoyee_dataframe(
    engine=Engine,
    minimum_salary=int,
    employment_status=str)-> pd.DataFrame:
    query = text(
        """
        SELECT
            e.employee_id,
            e.employee_name,
            COALESCE(d.department_name, '부서 미배정') AS department_name,
            e.job_title,
            e.salary,
            e.hire_date,
            e.employment_status,
            e.country_name
        FROM python_lab.employee AS e
        LEFT JOIN python_lab.department AS d 
            ON e.department_id = d.department_id
        WHERE e.salary >= :minimum_salary
            AND e.employment_status = :employment_status
        ORDER BY 
            e.salary DESC,
            e.employee_id ASC
            
        """
    )

    with engine.connect() as connection:
        filtered_df = pd.read_sql_query(
            sql=query,
            con=connection,
            params={
                'minimum_salary' : minimum_salary,
                'employment_status' : employment_status
            },
            parse_dates=['hire_date']
        )
    return filtered_df

def analyze_employee_dataframe(employee_df: pd.DataFrame) -> pd.DataFrame:
    result_df = (employee_df
                 .groupby('employment_status')
                 .agg(employee_count=('employee_id', 'count'),
                      average_salary=('salary', 'mean')
                      )
                 .sort_values('employee_count', ascending=False)
                 )
    result_df['average_salary'] = result_df['average_salary'].round().astype('int64')
    return result_df



def main() -> None:
    engine: Engine|None=None
    try:
        config = load_database_config()
        engine = create_database_engine(config)
        # print(engine)
        print_section('customer 테이블 조회')
        customer_df = load_customer_dataframe(engine)
        # print(customer_df.head())
        # print(customer_df.info())

        print_section('직원 부서 JOIN 결과 조회')
        employee_df = load_employee_join_dataframe(engine)
        # employee_df.info()
        filtered_df = load_filtered_empoyee_dataframe(
            engine=engine,
            minimum_salary=5000000,
            employment_status='active'
        )

        print(filtered_df.head())
        print(filtered_df.iloc[0])
        print()

        employee_status_summary_df = analyze_employee_dataframe(employee_df)
        print_section('재직 상태별 집계')
        print(employee_status_summary_df.head())

        employee_df.to_csv(OUTPUT_DIR / 'employee_df.csv', index=False)

    except FileNotFoundError as error:
        print(f'[설정 파일 오류]: {error}')
        sys.exit(1)

    except ValueError as error:
        print(f'[환경 변수 오류]: {error}')
        sys.exit(1)

    except SQLAlchemyError as error:
        print(f'[SQLAlchemy 또는 PostgreSQL 연결 오류]: {error}')
        sys.exit(1)

    except psycopg.errors.UndefinedTable as error:
        print(f'[테이블 없음]: {error}')
        sys.exit(1)

    except Exception as error:
        print(f'[예상하지 못한 오류]: {error}')
        sys.exit(1)

    finally:
        if engine is not None:
            engine.dispose()

if __name__ == "__main__":
    main()