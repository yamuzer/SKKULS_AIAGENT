from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import Engine, URL, create_engine, text


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


st.set_page_config(
    page_title="Olist 주문 분석",
    page_icon="📦",
    layout="wide",
)


def load_database_config() -> dict[str, Any]:
    load_dotenv(ENV_PATH, override=True)

    required_keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]
    missing_keys = [key for key in required_keys if not os.getenv(key)]

    if missing_keys:
        raise ValueError(
            ".env 파일에 다음 설정이 없습니다: " + ", ".join(missing_keys)
        )

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "database": os.environ["DB_NAME"],
        "username": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


@st.cache_resource
def create_database_engine() -> Engine:
    config = load_database_config()
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )
    return create_engine(database_url, pool_pre_ping=True)


@st.cache_data(ttl=600)
def load_order_data() -> pd.DataFrame:
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

    engine = create_database_engine()
    with engine.connect() as connection:
        dataframe = pd.read_sql_query(
            sql=query,
            con=connection,
            parse_dates=date_columns,
        )

    return preprocess_order_data(dataframe)


def preprocess_order_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    result_df = dataframe.copy()

    result_df["order_date"] = result_df["order_purchase_timestamp"].dt.date
    result_df["order_month"] = (
        result_df["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    )
    result_df["delivery_days"] = (
        result_df["order_delivered_customer_date"]
        - result_df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86_400

    result_df["is_late_delivery"] = (
        result_df["order_delivered_customer_date"]
        > result_df["order_estimated_delivery_date"]
    ).astype("boolean")

    unknown_delivery_mask = (
        result_df["order_delivered_customer_date"].isna()
        | result_df["order_estimated_delivery_date"].isna()
    )
    result_df.loc[unknown_delivery_mask, "is_late_delivery"] = pd.NA

    return result_df


def apply_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("필터")

    min_date = dataframe["order_date"].min()
    max_date = dataframe["order_date"].max()

    selected_dates = st.sidebar.date_input(
        "주문 기간",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    state_options = sorted(dataframe["customer_state"].dropna().unique())
    selected_states = st.sidebar.multiselect(
        "지역",
        options=state_options,
        default=state_options,
    )

    status_options = sorted(dataframe["order_status"].dropna().unique())
    selected_statuses = st.sidebar.multiselect(
        "주문 상태",
        options=status_options,
        default=status_options,
    )

    filtered_df = dataframe.loc[
        dataframe["customer_state"].isin(selected_states)
        & dataframe["order_status"].isin(selected_statuses)
    ].copy()

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_df = filtered_df.loc[
            filtered_df["order_date"].between(start_date, end_date)
        ]

    return filtered_df


def render_kpis(dataframe: pd.DataFrame) -> None:
    total_orders = dataframe["order_id"].nunique()
    unique_customers = dataframe["customer_unique_id"].nunique()

    delivered_count = int((dataframe["order_status"] == "delivered").sum())
    delivered_rate = (
        delivered_count / total_orders * 100 if total_orders else 0
    )

    delivered_df = dataframe.loc[
        (dataframe["order_status"] == "delivered")
        & dataframe["delivery_days"].notna()
    ]
    average_delivery_days = delivered_df["delivery_days"].mean()

    late_delivery_rate = (
        delivered_df["is_late_delivery"].dropna().mean() * 100
        if not delivered_df.empty
        else 0
    )

    columns = st.columns(4)
    columns[0].metric("주문 건수", f"{total_orders:,}건")
    columns[1].metric("고객 수", f"{unique_customers:,}명")
    columns[2].metric("배송 완료율", f"{delivered_rate:.1f}%")
    columns[3].metric(
        "평균 배송기간",
        f"{average_delivery_days:.1f}일"
        if pd.notna(average_delivery_days)
        else "-",
        help=f"배송 지연률: {late_delivery_rate:.1f}%",
    )


def render_monthly_orders(dataframe: pd.DataFrame) -> None:
    monthly_df = (
        dataframe.groupby("order_month", as_index=False)
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_unique_id", "nunique"),
        )
        .sort_values("order_month")
    )

    st.subheader("월별 주문 추이")
    st.line_chart(
        monthly_df,
        x="order_month",
        y=["order_count", "customer_count"],
        x_label="주문 월",
        y_label="건수",
        color=["#3155A6", "#59A14F"],
        use_container_width=True,
    )


def render_order_status(dataframe: pd.DataFrame) -> None:
    status_df = (
        dataframe.groupby("order_status", as_index=False)
        .agg(order_count=("order_id", "nunique"))
        .sort_values("order_count", ascending=True)
    )

    st.subheader("주문 상태별 주문 건수")
    st.bar_chart(
        status_df,
        x="order_status",
        y="order_count",
        x_label="주문 상태",
        y_label="주문 건수",
        color="#4C78A8",
        use_container_width=True,
    )


def render_state_orders(dataframe: pd.DataFrame) -> None:
    state_df = (
        dataframe.groupby("customer_state", as_index=False)
        .agg(order_count=("order_id", "nunique"))
        .nlargest(10, "order_count")
        .sort_values("order_count", ascending=True)
    )

    st.subheader("주문 건수 상위 10개 지역")
    st.bar_chart(
        state_df,
        x="customer_state",
        y="order_count",
        x_label="지역",
        y_label="주문 건수",
        color="#59A14F",
        use_container_width=True,
    )


def render_delivery_distribution(dataframe: pd.DataFrame) -> None:
    delivery_df = dataframe.loc[
        (dataframe["order_status"] == "delivered")
        & dataframe["delivery_days"].notna()
    ].copy()

    if delivery_df.empty:
        st.info("선택한 조건에 배송 완료 데이터가 없습니다.")
        return

    upper_limit = delivery_df["delivery_days"].quantile(0.99)
    chart_df = delivery_df.loc[
        delivery_df["delivery_days"] <= upper_limit
    ].copy()

    chart_df["delivery_range"] = pd.cut(
        chart_df["delivery_days"],
        bins=20,
        precision=0,
    )

    distribution_df = (
        chart_df.groupby(
            "delivery_range",
            observed=True,
        )
        .size()
        .rename("order_count")
        .reset_index()
    )
    distribution_df["delivery_range"] = (
        distribution_df["delivery_range"].astype(str)
    )

    st.subheader("배송 소요일 분포")
    st.caption("상위 1% 이상치는 제외했습니다.")
    st.bar_chart(
        distribution_df,
        x="delivery_range",
        y="order_count",
        x_label="배송 소요일 구간",
        y_label="주문 건수",
        color="#F28E2B",
        use_container_width=True,
    )


def render_data_table(dataframe: pd.DataFrame) -> None:
    st.subheader("주문 상세 데이터")

    display_columns = [
        "order_id",
        "customer_unique_id",
        "customer_state",
        "customer_city",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "delivery_days",
        "is_late_delivery",
    ]

    display_df = dataframe[display_columns].copy()
    display_df["delivery_days"] = display_df["delivery_days"].round(1)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="필터링 결과 CSV 다운로드",
        data=csv_data,
        file_name="olist_filtered_orders.csv",
        mime="text/csv",
    )


def main() -> None:
    st.title("📦 Olist 주문 분석 대시보드")
    st.caption("PostgreSQL에 저장된 고객·주문 데이터를 분석합니다.")

    try:
        with st.spinner("PostgreSQL에서 데이터를 불러오는 중입니다."):
            order_df = load_order_data()
    except Exception as error:
        st.error(f"데이터를 불러오지 못했습니다: {error}")
        st.stop()

    filtered_df = apply_filters(order_df)

    if filtered_df.empty:
        st.warning("선택한 필터 조건에 해당하는 데이터가 없습니다.")
        st.stop()

    render_kpis(filtered_df)
    st.divider()

    left_column, right_column = st.columns(2)

    with left_column:
        render_monthly_orders(filtered_df)
        render_state_orders(filtered_df)

    with right_column:
        render_order_status(filtered_df)
        render_delivery_distribution(filtered_df)

    st.divider()
    render_data_table(filtered_df)


if __name__ == "__main__":
    main()