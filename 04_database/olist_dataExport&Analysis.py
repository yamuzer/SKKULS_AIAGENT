from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import matplotlib.pyplot as plt
from matplotlib import font_manager
# =============================================================================
# 기본 설정
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
OUTPUT_DIR = BASE_DIR / "output"
CHART_DIR = OUTPUT_DIR / "charts"

# =============================================================================
# 데이터베이스 연결
# =============================================================================

def load_database_config() -> dict[str, Any]:
    if not ENV_PATH.exists():
        raise FileNotFoundError(
            f".env 파일이 없습니다: {ENV_PATH}"
        )

    load_dotenv(
        dotenv_path=ENV_PATH,
        override=True,
    )

    required_keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_keys = [
        key
        for key in required_keys
        if not os.getenv(key)
    ]

    if missing_keys:
        raise ValueError(
            ".env 파일에 다음 설정이 없습니다: "
            + ", ".join(missing_keys)
        )

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "database": os.environ["DB_NAME"],
        "username": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


def create_database_engine(
    config: dict[str, Any],
) -> Engine:
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# =============================================================================
# 데이터 조회
# =============================================================================

def load_order_dataframe(engine: Engine) -> pd.DataFrame:
    """주문과 고객 데이터를 JOIN하여 가져온다."""

    query = text(
        """
        SELECT
            TRIM(o.order_id) AS order_id,
            TRIM(o.customer_id) AS customer_id,
            TRIM(c.customer_unique_id) AS customer_unique_id,
            c.customer_zip_code_prefix,
            c.customer_city,
            TRIM(c.customer_state) AS customer_state,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_approved_at,
            o.order_delivered_carrier_date,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date
        FROM olist_schema.olist_orders AS o
        INNER JOIN olist_schema.olist_customers AS c
            ON o.customer_id = c.customer_id
        ORDER BY o.order_purchase_timestamp
        """
    )

    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    with engine.connect() as connection:
        order_df = pd.read_sql_query(
            sql=query,
            con=connection,
            parse_dates=date_columns,
        )

    return order_df


# =============================================================================
# 데이터 전처리
# =============================================================================

def preprocess_order_dataframe(
    order_df: pd.DataFrame,
) -> pd.DataFrame:
    result_df = order_df.copy()

    # 주문 연월
    result_df["order_year_month"] = (
        result_df["order_purchase_timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    # 주문일부터 고객 배송 완료일까지 걸린 시간
    result_df["delivery_days"] = (
        result_df["order_delivered_customer_date"]
        - result_df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86_400

    # 예상 배송일과 실제 배송일 차이
    # 양수: 예정일보다 일찍 배송
    # 음수: 예정일보다 늦게 배송
    result_df["delivery_difference_days"] = (
        result_df["order_estimated_delivery_date"]
        - result_df["order_delivered_customer_date"]
    ).dt.total_seconds() / 86_400
    # 일반 bool이 아닌 Pandas nullable boolean 타입으로 생성
    result_df["is_late_delivery"] = (
        result_df["order_delivered_customer_date"]
        > result_df["order_estimated_delivery_date"]
    ).astype("boolean")

    # 배송 완료일이 없는 주문은 지연 여부를 알 수 없으므로 결측 처리
    missing_delivery_mask = (
        result_df["order_delivered_customer_date"].isna()
    )

    result_df.loc[
        missing_delivery_mask,
        "is_late_delivery",
    ] = pd.NA

    return result_df


# =============================================================================
# 데이터 분석
# =============================================================================

def analyze_order_status(
    order_df: pd.DataFrame,
) -> pd.DataFrame:
    """주문 상태별 주문 건수를 집계한다."""

    result_df = (
        order_df
        .groupby(
            "order_status",
            as_index=False,
        )
        .agg(
            order_count=("order_id", "count"),
            customer_count=(
                "customer_unique_id",
                "nunique",
            ),
        )
        .sort_values(
            "order_count",
            ascending=False,
        )
    )

    return result_df


def analyze_monthly_orders(
    order_df: pd.DataFrame,
) -> pd.DataFrame:
    """월별 주문 건수와 고객 수를 집계한다."""

    result_df = (
        order_df
        .groupby(
            "order_year_month",
            as_index=False,
        )
        .agg(
            order_count=("order_id", "count"),
            customer_count=(
                "customer_unique_id",
                "nunique",
            ),
        )
        .sort_values("order_year_month")
    )

    return result_df


def analyze_state_orders(
    order_df: pd.DataFrame,
) -> pd.DataFrame:
    """주별 주문 및 배송 성과를 집계한다."""

    delivered_df = order_df.loc[
        order_df["order_status"] == "delivered"
    ].copy()

    result_df = (
        delivered_df
        .groupby(
            "customer_state",
            as_index=False,
        )
        .agg(
            order_count=("order_id", "count"),
            customer_count=(
                "customer_unique_id",
                "nunique",
            ),
            average_delivery_days=(
                "delivery_days",
                "mean",
            ),
            late_delivery_count=(
                "is_late_delivery",
                lambda values: int(
                    values.fillna(False).sum()
                ),
            ),
        )
    )

    result_df["late_delivery_rate"] = (
        result_df["late_delivery_count"]
        / result_df["order_count"]
        * 100
    )

    result_df["average_delivery_days"] = (
        result_df["average_delivery_days"].round(2)
    )

    result_df["late_delivery_rate"] = (
        result_df["late_delivery_rate"].round(2)
    )

    result_df = result_df.sort_values(
        "order_count",
        ascending=False,
    )

    return result_df


def analyze_delivery_summary(
    order_df: pd.DataFrame,
) -> pd.DataFrame:
    """전체 배송 성과를 요약한다."""

    delivered_df = order_df.loc[
        (order_df["order_status"] == "delivered")
        & order_df["order_delivered_customer_date"].notna()
    ].copy()

    delivery_count = len(delivered_df)

    late_delivery_count = int(
        delivered_df["is_late_delivery"].sum()
    )

    result_df = pd.DataFrame(
        {
            "metric": [
                "배송 완료 주문",
                "평균 배송 소요일",
                "중앙값 배송 소요일",
                "지연 배송 주문",
                "지연 배송률",
            ],
            "value": [
                delivery_count,
                round(
                    delivered_df["delivery_days"].mean(),
                    2,
                ),
                round(
                    delivered_df["delivery_days"].median(),
                    2,
                ),
                late_delivery_count,
                round(
                    late_delivery_count
                    / delivery_count
                    * 100,
                    2,
                ),
            ],
        }
    )

    return result_df


# =============================================================================
# 결과 저장
# =============================================================================

def save_analysis_results(
    order_df: pd.DataFrame,
    order_status_df: pd.DataFrame,
    monthly_order_df: pd.DataFrame,
    state_order_df: pd.DataFrame,
    delivery_summary_df: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    order_df.to_csv(
        OUTPUT_DIR / "olist_order_detail.csv",
        index=False,
        encoding="utf-8-sig",
    )

    order_status_df.to_csv(
        OUTPUT_DIR / "order_status_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    monthly_order_df.to_csv(
        OUTPUT_DIR / "monthly_order_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    state_order_df.to_csv(
        OUTPUT_DIR / "state_order_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    delivery_summary_df.to_csv(
        OUTPUT_DIR / "delivery_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print_section("CSV 저장 완료")
    print(f"저장 위치: {OUTPUT_DIR}")


# =============================================================================
# 데이터 시각화
# =============================================================================

def configure_matplotlib() -> None:
    """운영체제에 설치된 한글 폰트를 설정한다."""

    available_fonts = {
        font.name
        for font in font_manager.fontManager.ttflist
    }

    preferred_fonts = [
        "Malgun Gothic",    # Windows
        "AppleGothic",      # macOS
        "NanumGothic",      # Linux
    ]

    for font_name in preferred_fonts:
        if font_name in available_fonts:
            plt.rcParams["font.family"] = font_name
            break

    plt.rcParams["axes.unicode_minus"] = False


def save_monthly_order_chart(
    monthly_order_df: pd.DataFrame,
) -> None:
    """월별 주문 추이를 선 그래프로 저장한다."""

    chart_df = monthly_order_df.copy()

    plt.figure(figsize=(12, 6))

    plt.plot(
        chart_df["order_year_month"],
        chart_df["order_count"],
        marker="o",
        linewidth=2,
        color="#3155A6",
    )

    plt.title(
        "월별 주문 건수 추이",
        fontsize=16,
        pad=15,
    )

    plt.xlabel("주문 연월")
    plt.ylabel("주문 건수")

    plt.xticks(
        rotation=45,
        ha="right",
    )

    plt.grid(
        axis="y",
        alpha=0.3,
    )

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "monthly_orders.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


def save_order_status_chart(
    order_status_df: pd.DataFrame,
) -> None:
    """주문 상태별 주문 건수를 막대그래프로 저장한다."""

    chart_df = (
        order_status_df
        .sort_values("order_count")
        .copy()
    )

    plt.figure(figsize=(10, 6))

    bars = plt.barh(
        chart_df["order_status"],
        chart_df["order_count"],
        color="#4C78A8",
    )

    plt.title(
        "주문 상태별 주문 건수",
        fontsize=16,
        pad=15,
    )

    plt.xlabel("주문 건수")
    plt.ylabel("주문 상태")

    plt.bar_label(
        bars,
        labels=[
            f"{value:,}"
            for value in chart_df["order_count"]
        ],
        padding=4,
    )

    plt.grid(
        axis="x",
        alpha=0.3,
    )

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "order_status.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


def save_state_order_chart(
    state_order_df: pd.DataFrame,
) -> None:
    """주문 건수가 많은 상위 10개 지역을 시각화한다."""

    chart_df = (
        state_order_df
        .nlargest(10, "order_count")
        .sort_values("order_count")
        .copy()
    )

    plt.figure(figsize=(10, 6))

    bars = plt.barh(
        chart_df["customer_state"],
        chart_df["order_count"],
        color="#59A14F",
    )

    plt.title(
        "주문 건수 상위 10개 지역",
        fontsize=16,
        pad=15,
    )

    plt.xlabel("배송 완료 주문 건수")
    plt.ylabel("지역 코드")

    plt.bar_label(
        bars,
        labels=[
            f"{value:,}"
            for value in chart_df["order_count"]
        ],
        padding=4,
    )

    plt.grid(
        axis="x",
        alpha=0.3,
    )

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "top_10_states.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


def save_delivery_distribution_chart(
    order_df: pd.DataFrame,
) -> None:
    """배송 소요일 분포를 히스토그램으로 저장한다."""

    delivery_days = (
        order_df
        .loc[
            (order_df["order_status"] == "delivered")
            & order_df["delivery_days"].notna(),
            "delivery_days",
        ]
    )

    # 극단적인 이상치 때문에 그래프가 눌리는 것을 방지한다.
    upper_limit = delivery_days.quantile(0.99)

    chart_data = delivery_days.loc[
        delivery_days <= upper_limit
    ]

    average_delivery_days = chart_data.mean()
    median_delivery_days = chart_data.median()

    plt.figure(figsize=(10, 6))

    plt.hist(
        chart_data,
        bins=30,
        color="#F28E2B",
        edgecolor="white",
        alpha=0.85,
    )

    plt.axvline(
        average_delivery_days,
        color="#D62728",
        linestyle="--",
        linewidth=2,
        label=(
            f"평균 {average_delivery_days:.1f}일"
        ),
    )

    plt.axvline(
        median_delivery_days,
        color="#3155A6",
        linestyle=":",
        linewidth=2,
        label=(
            f"중앙값 {median_delivery_days:.1f}일"
        ),
    )

    plt.title(
        "배송 소요일 분포",
        fontsize=16,
        pad=15,
    )

    plt.xlabel("배송 소요일")
    plt.ylabel("주문 건수")

    plt.legend()

    plt.grid(
        axis="y",
        alpha=0.3,
    )

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "delivery_days_distribution.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


def create_visualizations(
    order_df: pd.DataFrame,
    order_status_df: pd.DataFrame,
    monthly_order_df: pd.DataFrame,
    state_order_df: pd.DataFrame,
) -> None:
    """분석 결과를 차트로 생성한다."""

    configure_matplotlib()

    CHART_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_monthly_order_chart(
        monthly_order_df=monthly_order_df,
    )

    save_order_status_chart(
        order_status_df=order_status_df,
    )

    save_state_order_chart(
        state_order_df=state_order_df,
    )

    save_delivery_distribution_chart(
        order_df=order_df,
    )

    print_section("데이터 시각화 완료")
    print(f"차트 저장 위치: {CHART_DIR}")

    for chart_path in sorted(CHART_DIR.glob("*.png")):
        print(f"  - {chart_path.name}")



# =============================================================================
# 프로그램 실행
# =============================================================================

def main() -> None:
    engine: Engine | None = None

    try:
        config = load_database_config()
        engine = create_database_engine(config)

        print_section("데이터베이스 조회")

        order_df = load_order_dataframe(engine)

        print(f"조회된 데이터: {len(order_df):,}건")
        print()
        print(order_df.head())

        print_section("데이터 전처리")

        order_df = preprocess_order_dataframe(order_df)

        print(order_df.info())

        print_section("주문 상태별 분석")

        order_status_df = analyze_order_status(order_df)
        print(order_status_df)

        print_section("월별 주문 분석")

        monthly_order_df = analyze_monthly_orders(order_df)
        print(monthly_order_df.tail(10))

        print_section("지역별 주문 및 배송 분석")

        state_order_df = analyze_state_orders(order_df)
        print(state_order_df.head(10))

        print_section("전체 배송 분석")

        delivery_summary_df = analyze_delivery_summary(
            order_df
        )
        print(delivery_summary_df)

        save_analysis_results(
            order_df=order_df,
            order_status_df=order_status_df,
            monthly_order_df=monthly_order_df,
            state_order_df=state_order_df,
            delivery_summary_df=delivery_summary_df,
        )

        create_visualizations(
            order_df=order_df,
            order_status_df=order_status_df,
            monthly_order_df=monthly_order_df,
            state_order_df=state_order_df,
        )
    except FileNotFoundError as error:
        print(f"[파일 오류] {error}")
        sys.exit(1)

    except ValueError as error:
        print(f"[환경변수 오류] {error}")
        sys.exit(1)

    except SQLAlchemyError as error:
        print(f"[SQLAlchemy 또는 PostgreSQL 오류] {error}")

        if getattr(error, "orig", None) is not None:
            print(f"[PostgreSQL 원본 오류] {error.orig}")

        sys.exit(1)

    except Exception as error:
        print(f"[예상하지 못한 오류] {error}")
        sys.exit(1)

    finally:
        if engine is not None:
            engine.dispose()

if __name__ == "__main__":
    main()