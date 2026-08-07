import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# sample_sales_data.csv


# ------------------------------------------------------------
# 1. 페이지 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="matplotlib 시각화 대시보드",
    layout="wide"
)


# ------------------------------------------------------------
# 2. matplotlib 한글 설정
# ------------------------------------------------------------
# Windows에서는 Malgun Gothic이 일반적으로 사용 가능하다.
# Mac에서는 AppleGothic, Linux에서는 NanumGothic이 필요할 수 있다.
# 아래 설정은 가능한 폰트를 순서대로 시도하는 방식이다.
# ------------------------------------------------------------
plt.rcParams["font.family"] = ["Malgun Gothic", "AppleGothic", "NanumGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ------------------------------------------------------------
# 3. 제목 영역
# ------------------------------------------------------------
st.title("실습 matplotlib 시각화 대시보드")

st.write(
    """
    이번 실습에서는 업로드한 매출 데이터를 필터링한 뒤  
    matplotlib 그래프를 이용해 시각화 대시보드를 만듭니다.

    시각화 항목:
    - 월별 매출 추이
    - 지역별 매출
    - 카테고리별 매출
    - 고객등급별 매출
    - 매출 분포
    """
)


# ------------------------------------------------------------
# 4. CSV 파일 읽기 함수
# ------------------------------------------------------------
def read_csv_file(uploaded_file):
    """
    업로드된 CSV 파일을 pandas DataFrame으로 읽어오는 함수
    """

    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        return df, "utf-8-sig"

    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="cp949")
        return df, "cp949"


# ------------------------------------------------------------
# 5. 날짜 컬럼 자동 변환 함수
# ------------------------------------------------------------
def try_convert_datetime_columns(df):
    """
    컬럼명에 날짜, 일자, date가 포함되어 있으면
    datetime 타입으로 변환을 시도한다.
    """

    converted_df = df.copy()
    converted_columns = []

    for column in converted_df.columns:
        column_text = str(column)
        column_lower = column_text.lower()

        is_date_column = (
            "날짜" in column_text
            or "일자" in column_text
            or "date" in column_lower
        )

        if is_date_column:
            try:
                converted_df[column] = pd.to_datetime(converted_df[column])
                converted_columns.append(column)
            except Exception:
                pass

    return converted_df, converted_columns


# ------------------------------------------------------------
# 6. 컬럼 타입 분류 함수
# ------------------------------------------------------------
def classify_columns(df):
    """
    숫자형, 범주형, 날짜형 컬럼을 분류한다.
    """

    numeric_columns = df.select_dtypes(
        include=["int64", "float64", "int32", "float32"]
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    datetime_columns = df.select_dtypes(
        include=["datetime64[ns]"]
    ).columns.tolist()

    return numeric_columns, categorical_columns, datetime_columns


# ------------------------------------------------------------
# 7. 후보 컬럼 자동 탐색 함수
# ------------------------------------------------------------
def find_column_by_candidates(df, candidates):
    """
    후보 컬럼명 목록 중 DataFrame에 존재하는 첫 번째 컬럼명을 반환한다.
    """

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    return None


# ------------------------------------------------------------
# 8. 그래프 생성 함수: 월별 매출 추이
# ------------------------------------------------------------
def draw_monthly_sales_chart(chart_df, date_col, sales_col):
    """
    월별 매출 추이 선그래프를 생성한다.
    """
    monthly_sales = chart_df.copy()
    monthly_sales['주문월'] = monthly_sales[date_col].dt.to_period('M').astype(str)

    monthly_summary = (
        monthly_sales
        .groupby('주문월')[sales_col]
        .sum()
        .reset_index()
        .sort_values('주문월')
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(monthly_summary['주문월'], monthly_summary[sales_col], marker='o')
    ax.set_title('월별 매출 추이')
    ax.set_xlabel('주문월')
    ax.set_ylabel('매출 합계')

    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, axis="y", alpha=0.3)

    return fig, monthly_summary





# ------------------------------------------------------------
# 9. 그래프 생성 함수: 범주형 기준 매출 막대그래프
# ------------------------------------------------------------
def draw_group_sales_bar_chart(chart_df, group_col, sales_col, title):
    """
    범주형 컬럼 기준 매출 합계 막대그래프를 생성한다.
    """

    group_summary = (
        chart_df
        .groupby(group_col, dropna=False)[sales_col]
        .sum()
        .reset_index()

        .sort_values(sales_col, ascending=False)
    )

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(
        group_summary[group_col].astype(str),
        group_summary[sales_col]
    )

    ax.set_title(title)
    ax.set_xlabel(group_col)
    ax.set_ylabel("매출 합계")

    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.3)

    return fig, group_summary


# ------------------------------------------------------------
# 10. 그래프 생성 함수: 매출 분포 히스토그램
# ------------------------------------------------------------
def draw_sales_histogram(chart_df, sales_col, bins):
    """
    매출 분포 히스토그램을 생성한다.
    """

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.hist(
        chart_df[sales_col].dropna(),
        bins=bins
    )

    ax.set_title("매출 분포")
    ax.set_xlabel("매출")
    ax.set_ylabel("데이터 수")

    ax.grid(True, axis="y", alpha=0.3)

    return fig


# ------------------------------------------------------------
# 11. 사이드바 - CSV 업로드
# ------------------------------------------------------------
st.sidebar.title("데이터 업로드")

uploaded_file = st.sidebar.file_uploader(
    "CSV 파일을 업로드하세요",
    type=["csv"]
)

st.sidebar.write("---")

st.sidebar.write(
    """
    권장 파일:
    - 실습 04에서 생성한 sample_sales_data.csv
    """
)


# ------------------------------------------------------------
# 12. 파일 미업로드 처리
# ------------------------------------------------------------
if uploaded_file is None:
    st.info("왼쪽 사이드바에서 CSV 파일을 업로드하세요.")

    st.subheader("이번 실습에서 만들 시각화")

    st.write(
        """
        1. 월별 매출 추이 선그래프  
        2. 지역별 매출 막대그래프  
        3. 카테고리별 매출 막대그래프  
        4. 고객등급별 매출 막대그래프  
        5. 매출 분포 히스토그램  
        """
    )

    st.stop()


# ------------------------------------------------------------
# 13. CSV 읽기
# ------------------------------------------------------------
try:
    df, used_encoding = read_csv_file(uploaded_file)

except Exception as error:
    st.error("CSV 파일을 읽는 중 오류가 발생했습니다.")
    st.write(error)
    st.stop()


# ------------------------------------------------------------
# 14. 날짜 컬럼 변환 및 컬럼 분류
# ------------------------------------------------------------
df, converted_datetime_columns = try_convert_datetime_columns(df)

numeric_columns, categorical_columns, datetime_columns = classify_columns(df)


# ------------------------------------------------------------
# 15. 주요 컬럼 자동 탐색
# ------------------------------------------------------------
date_column = find_column_by_candidates(
    df,
    ["주문일자", "날짜", "일자", "date", "Date"]
)

sales_column = find_column_by_candidates(
    df,
    ["매출", "판매금액", "주문금액", "금액", "sales", "Sales"]
)

region_column = find_column_by_candidates(
    df,
    ["지역", "권역", "도시", "region", "Region"]
)

category_column = find_column_by_candidates(
    df,
    ["카테고리", "분류", "상품군", "category", "Category"]
)

grade_column = find_column_by_candidates(
    df,
    ["고객등급", "등급", "grade", "Grade"]
)

channel_column = find_column_by_candidates(
    df,
    ["판매채널", "채널", "channel", "Channel"]
)


# ------------------------------------------------------------
# 16. 필수 컬럼 확인
# ------------------------------------------------------------
if sales_column is None:
    st.error("매출 컬럼을 찾지 못했습니다. 매출, 판매금액, 주문금액, 금액 중 하나의 컬럼이 필요합니다.")
    st.stop()

if sales_column not in numeric_columns:
    st.error(f"`{sales_column}` 컬럼이 숫자형이 아닙니다. 숫자형 매출 컬럼이 필요합니다.")
    st.stop()


# ------------------------------------------------------------
# 17. 사이드바 - 필터 설정
# ------------------------------------------------------------
st.sidebar.title("필터 설정")

filtered_df = df.copy()


# ------------------------------------------------------------
# 17-1. 날짜 필터
# ------------------------------------------------------------
if date_column is not None and date_column in datetime_columns:
    min_date = df[date_column].min().date()
    max_date = df[date_column].max().date()

    selected_date_range = st.sidebar.date_input(
        "날짜 범위 선택",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range

        filtered_df = filtered_df[
            (filtered_df[date_column].dt.date >= start_date)
            & (filtered_df[date_column].dt.date <= end_date)
        ]


# ------------------------------------------------------------
# 17-2. 지역 필터
# ------------------------------------------------------------
if region_column is not None:
    region_options = sorted(df[region_column].dropna().unique().tolist())

    selected_regions = st.sidebar.multiselect(
        "지역 선택",
        options=region_options,
        default=region_options
    )

    filtered_df = filtered_df[
        filtered_df[region_column].isin(selected_regions)
    ]


# ------------------------------------------------------------
# 17-3. 카테고리 필터
# ------------------------------------------------------------
if category_column is not None:
    category_options = sorted(df[category_column].dropna().unique().tolist())

    selected_categories = st.sidebar.multiselect(
        "카테고리 선택",
        options=category_options,
        default=category_options
    )

    filtered_df = filtered_df[
        filtered_df[category_column].isin(selected_categories)
    ]


# ------------------------------------------------------------
# 17-4. 고객등급 필터
# ------------------------------------------------------------
if grade_column is not None:
    grade_options = sorted(df[grade_column].dropna().unique().tolist())

    selected_grades = st.sidebar.multiselect(
        "고객등급 선택",
        options=grade_options,
        default=grade_options
    )

    filtered_df = filtered_df[
        filtered_df[grade_column].isin(selected_grades)
    ]


# ------------------------------------------------------------
# 17-5. 판매채널 필터
# ------------------------------------------------------------
if channel_column is not None:
    channel_options = sorted(df[channel_column].dropna().unique().tolist())

    selected_channels = st.sidebar.multiselect(
        "판매채널 선택",
        options=channel_options,
        default=channel_options
    )

    filtered_df = filtered_df[
        filtered_df[channel_column].isin(selected_channels)
    ]


# ------------------------------------------------------------
# 17-6. 매출 범위 필터
# ------------------------------------------------------------
min_sales = int(df[sales_column].min())
max_sales = int(df[sales_column].max())

if min_sales < max_sales:
    selected_sales_range = st.sidebar.slider(
        "매출 범위 선택",
        min_value=min_sales,
        max_value=max_sales,
        value=(min_sales, max_sales),
        step=1000
    )

    filtered_df = filtered_df[
        (filtered_df[sales_column] >= selected_sales_range[0])
        & (filtered_df[sales_column] <= selected_sales_range[1])
    ]


# ------------------------------------------------------------
# 18. 메인 - KPI 요약
# ------------------------------------------------------------
st.subheader("1. 필터링 결과 요약")

original_row_count = len(df)
filtered_row_count = len(filtered_df)

if original_row_count > 0:
    filtered_ratio = filtered_row_count / original_row_count * 100
else:
    filtered_ratio = 0

if len(filtered_df) > 0:
    total_sales = filtered_df[sales_column].sum()
    average_sales = filtered_df[sales_column].mean()
    max_sales_value = filtered_df[sales_column].max()
else:
    total_sales = 0
    average_sales = 0
    max_sales_value = 0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="원본 행 수",
        value=f"{original_row_count:,}행"
    )

with col2:
    st.metric(
        label="필터 후 행 수",
        value=f"{filtered_row_count:,}행"
    )

with col3:
    st.metric(
        label="총 매출",
        value=f"{total_sales:,.0f}원"
    )

with col4:
    st.metric(
        label="평균 매출",
        value=f"{average_sales:,.0f}원"
    )

with col5:
    st.metric(
        label="최고 매출",
        value=f"{max_sales_value:,.0f}원"
    )

st.write(f"CSV 인코딩: `{used_encoding}`")

if len(converted_datetime_columns) > 0:
    st.success(f"날짜형 변환 컬럼: {converted_datetime_columns}")


# ------------------------------------------------------------
# 19. 데이터 없음 처리
# ------------------------------------------------------------
if len(filtered_df) == 0:
    st.warning("현재 필터 조건에 해당하는 데이터가 없습니다. 사이드바에서 조건을 완화하세요.")
    st.stop()


# ------------------------------------------------------------
# 20. 탭 구성
# ------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "월별 매출 추이",
        "지역별 매출",
        "카테고리별 매출",
        "고객등급/채널별 매출",
        "매출 분포"
    ]
)


# ------------------------------------------------------------
# 20-1. 월별 매출 추이
# ------------------------------------------------------------
with tab1:
    st.subheader('월별 매출 추이')
    if date_column is None or date_column not in datetime_columns:
        st.warning('날짜형 컬럼이 없어 월별 매출 추이를 그릴 수 없습니다.')
    else :
        fig, monthly_summary = draw_monthly_sales_chart(
            filtered_df,
            date_column,
            sales_column
        )
        st.pyplot(fig)



# ------------------------------------------------------------
# 20-2. 지역별 매출
# ------------------------------------------------------------
with tab2:
    st.subheader("지역별 매출")

    if region_column is None:
        st.warning("지역 컬럼을 찾지 못했습니다.")

    else:
        fig, region_summary = draw_group_sales_bar_chart(
            filtered_df,
            region_column,
            sales_column,
            "지역별 매출 합계"
        )

        st.pyplot(fig)

        st.dataframe(
            region_summary,
            use_container_width=True
        )

        if len(region_summary) > 0:
            top_region = region_summary.iloc[0][region_column]
            top_region_sales = region_summary.iloc[0][sales_column]

            st.write(
                f"""
                현재 필터 조건에서 매출이 가장 높은 지역은 **{top_region}**이며,  
                해당 지역의 총매출은 **{top_region_sales:,.0f}원**입니다.
                """
            )


# ------------------------------------------------------------
# 20-3. 카테고리별 매출
# ------------------------------------------------------------
with tab3:
    st.subheader("카테고리별 매출")

    if category_column is None:
        st.warning("카테고리 컬럼을 찾지 못했습니다.")

    else:
        fig, category_summary = draw_group_sales_bar_chart(
            filtered_df,
            category_column,
            sales_column,
            "카테고리별 매출 합계"
        )

        st.pyplot(fig)

        st.dataframe(
            category_summary,
            use_container_width=True
        )

        if len(category_summary) > 0:
            top_category = category_summary.iloc[0][category_column]
            top_category_sales = category_summary.iloc[0][sales_column]

            st.write(
                f"""
                현재 필터 조건에서 매출이 가장 높은 카테고리는 **{top_category}**이며,  
                해당 카테고리의 총매출은 **{top_category_sales:,.0f}원**입니다.
                """
            )


# ------------------------------------------------------------
# 20-4. 고객등급/채널별 매출
# ------------------------------------------------------------
with tab4:
    st.subheader("고객등급/채널별 매출")

    group_options = []

    if grade_column is not None:
        group_options.append(grade_column)

    if channel_column is not None:
        group_options.append(channel_column)

    if len(group_options) == 0:
        st.warning("고객등급 또는 판매채널 컬럼을 찾지 못했습니다.")

    else:
        selected_group_column = st.selectbox(
            "그래프로 볼 기준 선택",
            options=group_options
        )

        fig, group_summary = draw_group_sales_bar_chart(
            filtered_df,
            selected_group_column,
            sales_column,
            f"{selected_group_column}별 매출 합계"
        )

        st.pyplot(fig)

        st.dataframe(
            group_summary,
            use_container_width=True
        )

        if len(group_summary) > 0:
            top_value = group_summary.iloc[0][selected_group_column]
            top_value_sales = group_summary.iloc[0][sales_column]

            st.write(
                f"""
                현재 필터 조건에서 `{selected_group_column}` 기준 매출이 가장 높은 값은  
                **{top_value}**이며, 총매출은 **{top_value_sales:,.0f}원**입니다.
                """
            )


# ------------------------------------------------------------
# 20-5. 매출 분포
# ------------------------------------------------------------
with tab5:
    st.subheader("매출 분포 히스토그램")

    bin_count = st.slider(
        "히스토그램 구간 수",
        min_value=5,
        max_value=50,
        value=20,
        step=5
    )

    fig = draw_sales_histogram(
        filtered_df,
        sales_column,
        bin_count
    )

    st.pyplot(fig)

    st.write(
        f"""
        현재 필터 조건에서 매출 평균은 **{filtered_df[sales_column].mean():,.0f}원**이고,  
        중앙값은 **{filtered_df[sales_column].median():,.0f}원**입니다.  
        최솟값은 **{filtered_df[sales_column].min():,.0f}원**,  
        최댓값은 **{filtered_df[sales_column].max():,.0f}원**입니다.
        """
    )


# ------------------------------------------------------------
# 21. 종합 해석
# ------------------------------------------------------------
st.subheader("2. 시각화 종합 요약")

summary_text = (
    f"원본 데이터 {original_row_count:,}행 중 현재 필터 조건에 해당하는 데이터는 "
    f"{filtered_row_count:,}행입니다. 전체의 {filtered_ratio:.1f}%가 분석 대상입니다. "
    f"필터링된 데이터의 총매출은 {total_sales:,.0f}원이며, "
    f"평균 주문 매출은 {average_sales:,.0f}원입니다."
)

st.write(summary_text)


# ------------------------------------------------------------
# 22. 수업 설명용 expander
# ------------------------------------------------------------
with st.expander("이번 실습에서 배운 핵심 개념 보기"):
    st.write(
        """
        이번 실습에서는 matplotlib 그래프를 Streamlit 화면에 출력했습니다.

        핵심 개념:

        1. plt.subplots()
        - 그래프를 그릴 도화지와 축을 만듭니다.

        2. ax.plot()
        - 선그래프를 그립니다.
        - 월별 매출 추이처럼 시간 흐름을 볼 때 사용합니다.

        3. ax.bar()
        - 막대그래프를 그립니다.
        - 지역별 매출, 카테고리별 매출처럼 그룹별 비교에 사용합니다.

        4. ax.hist()
        - 히스토그램을 그립니다.
        - 매출 값이 어떤 구간에 많이 분포하는지 볼 때 사용합니다.

        5. st.pyplot(fig)
        - matplotlib에서 만든 그래프를 Streamlit 화면에 출력합니다.

        6. groupby()
        - 그래프를 그리기 전 기준 컬럼별로 데이터를 집계할 때 사용합니다.
        """
    )

