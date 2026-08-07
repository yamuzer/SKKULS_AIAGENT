import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Streamlit 입력 위젯 실습",
    layout="wide"
)

st.title("실습 02. Streamlit 입력 위젯 + 조건 처리")

st.write(
    """
    이번 실습에서는 사용자가 직접 조건을 선택하고,
    선택한 조건에 따라 학생 성적 데이터를 필터링하는 앱을 만듭니다.
    """
)


# ------------------------------------------------------------
# 1. 학생 성적 데이터 생성
# ------------------------------------------------------------
student_data = {
    "이름": [
        "김민수", "이서연", "박지훈", "최유진", "정현우",
        "한지민", "오세훈", "강다은", "윤태호", "임수진",
        "송하늘", "문지호", "배수아", "남도윤", "신예린"
    ],
    "반": [
        "A반", "A반", "A반", "B반", "B반",
        "B반", "C반", "C반", "C반", "C반",
        "A반", "B반", "C반", "A반", "B반"
    ],
    "성별": [
        "남", "여", "남", "여", "남",
        "여", "남", "여", "남", "여",
        "여", "남", "여", "남", "여"
    ],
    "Python": [85, 92, 76, 88, 67, 95, 71, 84, 90, 79, 93, 74, 82, 69, 97],
    "Data": [78, 89, 82, 91, 73, 96, 68, 87, 94, 81, 90, 77, 85, 72, 95],
    "AI": [80, 94, 75, 86, 70, 98, 72, 85, 91, 77, 92, 79, 83, 71, 96],
}

df = pd.DataFrame(student_data)


# ------------------------------------------------------------
# 2. 파생 컬럼 생성
# ------------------------------------------------------------
df["총점"] = df["Python"] + df["Data"] + df["AI"]
df["평균"] = df["총점"] / 3


# ------------------------------------------------------------
# 3. 원본 데이터 출력
# ------------------------------------------------------------
st.subheader("1. 원본 학생 성적 데이터")
st.dataframe(df, use_container_width=True)


# ------------------------------------------------------------
# 4. 입력 위젯 영역
# ------------------------------------------------------------
st.subheader("2. 분석 조건 선택")
st.write(
    """
    아래 조건을 변경한 뒤 [분석 실행] 버튼을 누르면,
    선택한 조건에 맞는 학생만 필터링됩니다.
    """
)

class_options = sorted(df['반'].unique())
selected_classes = st.multiselect(
    label='분석할 반을 선택하세요',
    options=class_options,
    default=class_options
)

subject_options = ['Python', 'Data', 'AI']
selected_subject = st.selectbox(
    label='기준 과목을 선택하세요',
    options=subject_options,
)

selected_min_score = st.slider(
    label='선택한 과목의 최소 점수를 선택하세요',
    min_value=0,
    max_value=100,
    value=70,
    step=1
)

pass_score = st.number_input(
    label='합격 기준 평균 점수를 입력하세요.',
    min_value=0,
    max_value=100,
    value=80,
    step=1
)

gender = ['전체'] + sorted(df['성별'].unique())
selected_gender = st.radio(
    label='성별을 선택하세요',
    options=gender,
    horizontal=True
)

search_name = st.text_input(
    label='학생 이름을 검색하세요',
    placeholder='예: 김민수'
)


# ------------------------------------------------------------
# 5. 분석 실행 버튼
# ------------------------------------------------------------

run_analysis = st.button('분석 실행')

# ------------------------------------------------------------
# 6. 분석 실행
# ------------------------------------------------------------
if run_analysis:
    st.write(
        f'선택한 반: {selected_classes}, '
        f'선택 과목: {selected_subject}, '
        f'선택 성별: {selected_gender}'
    )
else:
    st.info('조건을 선택한 뒤 [분석 실행] 버튼을 눌러 주세요')
