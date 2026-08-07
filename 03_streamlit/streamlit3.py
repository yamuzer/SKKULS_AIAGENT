import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# 1. 페이지 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="Streamlit 레이아웃 대시보드",
    layout="wide"
)


# ------------------------------------------------------------
# 2. 샘플 학생 성적 데이터 생성
# ------------------------------------------------------------
student_data = {
    "이름": [
        "김민수", "이서연", "박지훈", "최유진", "정현우",
        "한지민", "오세훈", "강다은", "윤태호", "임수진",
        "송하늘", "문지호", "배수아", "남도윤", "신예린",
        "유하준", "장서윤", "백민재", "노가은", "서지우"
    ],
    "반": [
        "A반", "A반", "A반", "B반", "B반",
        "B반", "C반", "C반", "C반", "C반",
        "A반", "B반", "C반", "A반", "B반",
        "A반", "B반", "C반", "A반", "C반"
    ],
    "성별": [
        "남", "여", "남", "여", "남",
        "여", "남", "여", "남", "여",
        "여", "남", "여", "남", "여",
        "남", "여", "남", "여", "남"
    ],
    "Python": [85, 92, 76, 88, 67, 95, 71, 84, 90, 79, 93, 74, 82, 69, 97, 81, 86, 72, 94, 78],
    "Data": [78, 89, 82, 91, 73, 96, 68, 87, 94, 81, 90, 77, 85, 72, 95, 83, 88, 75, 92, 80],
    "AI": [80, 94, 75, 86, 70, 98, 72, 85, 91, 77, 92, 79, 83, 71, 96, 84, 90, 76, 93, 82]
}

df = pd.DataFrame(student_data)

df["총점"] = df["Python"] + df["Data"] + df["AI"]
df["평균"] = df["총점"] / 3


# ------------------------------------------------------------
# 3. 사이드바 구성
# ------------------------------------------------------------
# 사이드바는 화면 왼쪽에 고정되는 설정 영역이다.
# 대시보드에서는 필터, 메뉴, 옵션 선택 등을 사이드바에 배치하는 경우가 많다.
# ------------------------------------------------------------

st.sidebar.title('분석 설정')
st.sidebar.write(
'''
이 영역은 사용자가 분석 조건을 선택하는 공간입니다.
'''
)

class_options = sorted(df["반"].unique())
selected_classes = st.sidebar.multiselect(
    "분석할 반 선택",
    options=class_options,
    default=class_options
)

gender_options = ["전체"] + sorted(df["성별"].unique())
selected_gender = st.sidebar.selectbox(
    "성별 선택",
    options=gender_options
)

subject_options = ["Python", "Data", "AI", "평균"]
selected_subject = st.sidebar.selectbox(
    "주요 분석 기준 선택",
    options=subject_options
)

min_average = st.sidebar.slider(
    "최소 평균 점수",
    min_value=0,
    max_value=100,
    value=70,
    step=1
)

show_raw_data = st.sidebar.checkbox(
    "원본 데이터 보기",
    value=True
)


# ------------------------------------------------------------
# 4. 필터 조건 적용
# ------------------------------------------------------------
filtered_df = df.copy()

filtered_df = filtered_df[
    filtered_df["반"].isin(selected_classes)
]

if selected_gender != "전체":
    filtered_df = filtered_df[
        filtered_df["성별"] == selected_gender
    ]

filtered_df = filtered_df[
    filtered_df["평균"] >= min_average
]


# ------------------------------------------------------------
# 5. 메인 제목 영역
# ------------------------------------------------------------
st.title("실습 03. Streamlit 레이아웃 대시보드")

st.write(
    """
    이번 실습에서는 Streamlit의 레이아웃 기능을 이용해  
    학생 성적 데이터를 대시보드 형태로 구성합니다.
    """
)


# ------------------------------------------------------------
# 6. KPI 카드 영역
# ------------------------------------------------------------
# st.columns를 사용하면 화면을 여러 개의 세로 영역으로 나눌 수 있다.
# st.metric은 숫자 지표를 카드처럼 보여줄 때 사용한다.
# ------------------------------------------------------------
st.subheader("1. 주요 지표 요약")

total_students = len(filtered_df)

if total_students > 0:
    average_score = filtered_df["평균"].mean()
    max_score = filtered_df["평균"].max()
    min_score = filtered_df["평균"].min()
    top_student = filtered_df.loc[filtered_df["평균"].idxmax(), "이름"]
else:
    average_score = 0
    max_score = 0
    min_score = 0
    top_student = "-"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="조회 학생 수",
        value=f"{total_students}명"
    )

with col2:
    st.metric(
        label="평균 점수",
        value=f"{average_score:.1f}점"
    )

with col3:
    st.metric(
        label="최고 평균",
        value=f"{max_score:.1f}점"
    )

with col4:
    st.metric(
        label="최고 학생",
        value=top_student
    )


# ------------------------------------------------------------
# 7. 탭 구성
# ------------------------------------------------------------
# st.tabs를 사용하면 하나의 화면 안에서 여러 섹션을 나눌 수 있다.
# ------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        '데이터 보기',
        '반별 통계',
        '과목별 통계',
        '분석 설명'
    ]
)


# ------------------------------------------------------------
# 7-1. 데이터 보기 탭
# ------------------------------------------------------------
with tab1:
    st.subheader('필터링된 데이터')
    st.write(f'현재 조건에 맞는 학생은 {len(filtered_df)}명입니다.')

    if len(filtered_df) == 0:
        st.warning('현재 선택한 조건에 해당하는 데이터가 없습니다.')
    else:
        st.dataframe(
            filtered_df,
            use_container_width=True
        )

    if show_raw_data:
        with st.expander('원본 데이터 확인'):
            st.dataframe(
                df,
                use_container_width=True
            )
# ------------------------------------------------------------
# 7-2. 반별 통계 탭
# ------------------------------------------------------------
with tab2:
    st.subheader("반별 평균 점수")

    if len(filtered_df) == 0:
        st.warning("통계를 계산할 데이터가 없습니다.")
    else:
        class_summary = filtered_df.groupby("반")[["Python", "Data", "AI", "평균"]].mean()
        class_count = filtered_df.groupby("반")["이름"].count()

        class_summary["학생 수"] = class_count

        st.dataframe(
            class_summary,
            use_container_width=True
        )

        best_class = class_summary["평균"].idxmax()
        best_class_score = class_summary.loc[best_class, "평균"]

        st.success(
            f"현재 조건에서 평균 점수가 가장 높은 반은 {best_class}이며, "
            f"평균 점수는 {best_class_score:.1f}점입니다."
        )


# ------------------------------------------------------------
# 7-3. 과목별 통계 탭
# ------------------------------------------------------------
with tab3:
    st.subheader("과목별 평균 점수")

    if len(filtered_df) == 0:
        st.warning("통계를 계산할 데이터가 없습니다.")
    else:
        subject_summary = filtered_df[["Python", "Data", "AI"]].mean()

        subject_summary_df = subject_summary.reset_index()
        subject_summary_df.columns = ["과목", "평균 점수"]

        st.dataframe(
            subject_summary_df,
            use_container_width=True
        )

        best_subject = subject_summary.idxmax()
        best_subject_score = subject_summary.max()

        st.info(
            f"현재 조건에서 평균 점수가 가장 높은 과목은 {best_subject}이며, "
            f"평균 점수는 {best_subject_score:.1f}점입니다."
        )

        st.subheader("선택 기준 컬럼 상위 학생")

        top_students_by_subject = filtered_df.sort_values(
            by=selected_subject,
            ascending=False
        ).head(5)

        st.dataframe(
            top_students_by_subject[["이름", "반", "성별", selected_subject, "평균"]],
            use_container_width=True
        )


# ------------------------------------------------------------
# 7-4. 분석 설명 탭
# ------------------------------------------------------------
with tab4:
    st.subheader("이번 실습에서 배운 내용")

    st.write(
        """
        이번 실습은 화면 레이아웃을 구성하는 것이 핵심입니다.

        Streamlit 앱이 단순한 출력 화면에서 대시보드처럼 보이려면  
        다음 기능들을 조합해야 합니다.
        """
    )

    st.markdown(
        """
        - `st.sidebar`: 분석 조건이나 메뉴를 왼쪽에 배치
        - `st.columns`: KPI 지표를 가로로 배치
        - `st.metric`: 숫자 지표를 카드 형태로 표시
        - `st.tabs`: 여러 분석 화면을 탭으로 분리
        - `st.expander`: 상세 내용을 접었다 펼칠 수 있게 구성
        - `st.dataframe`: 표 데이터를 화면에 표시
        """
    )

    with st.expander("수업 진행 팁"):
        st.write(
            """
            이 실습을 설명할 때는 Streamlit 문법을 하나씩 외우게 하기보다,
            화면을 어떻게 나누면 사용자가 보기 편한지 중심으로 설명하는 것이 좋습니다.

            예를 들어:
            1. 설정은 sidebar에 둔다.
            2. 핵심 숫자는 metric 카드로 보여준다.
            3. 상세 데이터는 tab 안에 넣는다.
            4. 보조 설명은 expander 안에 넣는다.
            """
        )


# ------------------------------------------------------------
# 8. 하단 요약
# ------------------------------------------------------------
st.divider()

st.write(
    """
    아래 부분입니다.
    """
)