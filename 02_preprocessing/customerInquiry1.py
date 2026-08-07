from pathlib import Path
import html
import re
import unicodedata

import pandas as pd

# 현재 실행 중인 파일의 위치를 기준으로 경로 설정
BASE_DIR = Path(__file__).resolve().parent

# 입력 CSV 파일
INPUT_CSV_PATH = BASE_DIR / 'data' / 'customer_inquiries_raw.csv'

# 출력 폴더 및 저장 경로
OUTPUT_DIR = BASE_DIR / 'output'
OUTPUT_CSV_PATH = OUTPUT_DIR / 'customer_inquiries.csv'

# ------------------------------------------------------------------
# 텍스트 전처리에 사용할 정규표현식
# ------------------------------------------------------------------

# HTML 태그(<p>, <div> 등)
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

# URL
URL_TAG_PATTERN = re.compile(r'https?://[^\s]+', re.IGNORECASE)

# 연속된 공백 또는 탭
MULTIPLE_SPACE_PATTERN = re.compile(r'[ \t]+')

# 연속된 줄바꿈
MULTIPLE_NEWLINE_PATTERN = re.compile(r'\n+')


def has_html(text: str) -> bool:
    """HTML 태그 포함 여부"""
    return bool(HTML_TAG_PATTERN.search(text))


def has_url(text: str) -> bool:
    """URL 포함 여부"""
    return bool(URL_TAG_PATTERN.search(text))


def has_line_break(text: str) -> bool:
    """줄바꿈 문자 포함 여부"""

    return bool('\n' in text or '\r' in text)


def has_extra_whitespace(text: str) -> bool:
    """불필요한 공백 존재 여부"""

    # 앞뒤 공백 확인
    if text != text.strip():
        return True


    if '\t' in text:
        return True

    # 공백이 2개 이상 연속되는 경우
    return bool(re.search(r' {2,}', text))


def clean_inquiry_text(text: str) -> str:
    """
    고객 문의 텍스트 전처리

    처리 순서
    1. 결측치 처리
    2. 유니코드 정규화
    3. HTML 특수문자 복원
    4. HTML 태그 제거
    5. URL 치환
    6. 줄바꿈 제거
    7. 연속 공백 정리
    8. 앞뒤 공백 제거
    """

    # 1. 결측치는 빈 문자열로 처리
    if pd.isna(text):
        return ""

    cleaned_text = str(text)

    # 2. 유니코드 정규화
    # 전각 문자, 호환 문자 등을 비교하기 쉬운 형태로 통일
    cleaned_text = unicodedata.normalize('NFKD', cleaned_text)

    # 3. HTML 특수문자(&amp;, &lt; 등)를 원래 문자로 복원
    cleaned_text = html.unescape(cleaned_text)

    # 4. HTML 태그 제거
    cleaned_text = HTML_TAG_PATTERN.sub(" ", cleaned_text)

    # 5. URL을 [URL] 토큰으로 치환
    cleaned_text = URL_TAG_PATTERN.sub("[URL]", cleaned_text)

    # 6. 줄바꿈 통일 후 제거
    cleaned_text = cleaned_text.replace('\r\n', '\n').replace('\r', '\n')
    cleaned_text = MULTIPLE_NEWLINE_PATTERN.sub(' ', cleaned_text)

    # 7. 연속된 공백을 하나로 변경
    cleaned_text = MULTIPLE_SPACE_PATTERN.sub(' ', cleaned_text)

    # 8. 앞뒤 공백 제거
    cleaned_text = cleaned_text.strip()

    return cleaned_text


def main():
    # 입력 파일 존재 여부 확인
    if not INPUT_CSV_PATH.exists():
        print('입력 파일을 찾을 수 없습니다.')
        return

    # CSV 읽기
    inquiry_df = pd.read_csv(INPUT_CSV_PATH, encoding='utf-8')

    # 데이터 확인
    print(inquiry_df.head())

    # 원본 텍스트 보존
    inquiry_df['original_text'] = inquiry_df['inquiry_text']

    # 문자열 타입으로 변환
    text_series = (
        inquiry_df['original_text']
        .fillna('')
        .astype(str)
    )

    # 전처리 전 텍스트 특성 분석
    inquiry_df['had_html'] = text_series.apply(has_html)
    inquiry_df['had_url'] = text_series.apply(has_url)
    inquiry_df['had_line_break'] = text_series.apply(has_line_break)
    inquiry_df['had_extra_whitespace'] = text_series.apply(has_extra_whitespace)

    # 통계 출력
    print(f"HTML 포함: {int(inquiry_df['had_html'].sum())}")
    print(f"URL 포함: {int(inquiry_df['had_url'].sum())}")
    print(f"줄바꿈 포함: {int(inquiry_df['had_line_break'].sum())}")
    print(f"불필요한 공백 포함: {int(inquiry_df['had_extra_whitespace'].sum())}")

    # 전처리 전 문자열 길이
    inquiry_df['before_length'] = text_series.str.len()

    # 텍스트 전처리
    inquiry_df['clean_text'] = inquiry_df['original_text'].apply(clean_inquiry_text)

    # 전처리 후 문자열 길이
    inquiry_df['after_length'] = inquiry_df['clean_text'].str.len()

    # 기존 컬럼을 정제된 텍스트로 교체
    inquiry_df['inquiry_text'] = inquiry_df['clean_text']

    # 임시 컬럼 삭제
    # ※ 현재 코드는 오류 발생
    inquiry_df.drop(columns=['clean_text'], inplace=True)


    # 출력 폴더 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # CSV 저장
    inquiry_df.to_csv(
        OUTPUT_CSV_PATH,
        index=False,
        encoding='utf-8'
    )


# 프로그램 시작점
if __name__ == '__main__':
    main()