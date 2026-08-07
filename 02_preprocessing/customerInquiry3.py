from pathlib import Path
import re
import pandas as pd

# 현재 파이썬 파일이 위치한 디렉터리
BASE_DIR = Path(__file__).resolve().parent

# 데이터 입력/출력 폴더 경로
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'

# 입력 CSV 파일
INPUT_PATH = DATA_DIR / 'customer_inquiries_with_pii.csv'

# 개인정보 탐지 결과 저장 파일
DETECTION_OUTPUT_DIR = OUTPUT_DIR / 'pii_detection_results.csv'

# 문의별 개인정보 요약 결과 저장 파일
SUMMARY_OUTPUT_DIR = OUTPUT_DIR / 'inquiries_with_pii.csv'


# -------------------------------------------------
# 개인정보 탐지를 위한 정규표현식 패턴
# -------------------------------------------------
PII_PATTERNS = {

    # 이메일 주소
    # 예) test123@gmail.com
    'EMAIL': re.compile(
        r'(?<![A-Za-z0-9._%+-])'
        r'[A-Za-z0-9._%+-]+'
        r'@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
        r'(?![A-Za-z0-9-])'
    ),

    # 전화번호
    # 예)
    # 010-8989-4545
    # 02-123-4567
    # +1-202-123-4565
    # +33-6-12-34-56-78
    'PHONE': re.compile(
        r'(?<![A-Za-z0-9])'
        r'(?:'
        r'0\d{1,2}-\d{3,4}-\d{4}'
        r'|'
        r'\+\d{1,3}(?:-\d{1,4}){2,5}'
        r')'
        r'(?![A-Za-z0-9])'
    ),

    # IPv4 주소
    # 예) 192.168.0.1
    'IP_ADDRESS': re.compile(
        r'(?<!\d)'
        r'(?:\d{1,3}\.){3}\d{1,3}'
        r'(?!\d)'
    ),

    # 주문번호
    # 예) ORD-20250101-1234
    'ORDER_ID': re.compile(
        r'(?<![A-Za-z0-9])'
        r'ORD-\d{8}-\d{4}'
        r'(?![A-Za-z0-9])'
    ),

    # 고객번호
    # 예) CUST-123456
    'CUSTOMER_ID': re.compile(
        r'(?<![A-Za-z0-9])'
        r'CUST-\d{6}'
        r'(?![A-Za-z0-9])'
    ),
}


def create_masked_value(
    pii_type: str,
    detection_value: str,
) -> str:
    """
    탐지된 개인정보를 화면에 표시할 수 있도록
    일부만 남기고 마스킹한 문자열을 반환한다.
    """

    # 이메일 : 아이디 앞 2글자만 노출
    if pii_type == 'EMAIL':
        local_part, domain = detection_value.split("@", maxsplit=1)
        visible = local_part[:2]
        return f"{visible}***@{domain}"

    # 전화번호 : 마지막 4자리만 노출
    if pii_type == 'PHONE':
        digits = re.sub(r'\D', "", detection_value)

        if len(digits) >= 4:
            return f"***-****-{digits[-4:]}*****"

        return "[PHONE]"

    # IP : 앞 두 옥텟만 노출
    if pii_type == 'IP_ADDRESS':
        parts = detection_value.split('.')

        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"

        return "[IP]"

    # 주문번호 : 마지막 4자리 마스킹
    if pii_type == 'ORDER_ID':
        return detection_value[:13] + '****'

    # 고객번호 전체 마스킹
    if pii_type == 'CUSTOMER_ID':
        return 'CUST-******'

    # 정의되지 않은 개인정보 유형
    return "[PII]"


def detect_pii_from_text(
    inquiry_id: str,
    text
) -> list[dict]:
    """
    고객 문의 한 건의 본문에서 개인정보를 탐지한다.

    반환 정보
    ----------
    inquiry_id
    pii_type
    detected_value
    masked_preview
    start_position
    end_position
    """

    # 결측치는 탐지 대상이 아님
    if pd.isna(text):
        return []

    text = str(text)

    # 탐지 결과 저장 리스트
    detection_results = []

    # 등록된 모든 개인정보 패턴 검사
    for pii_type, pattern in PII_PATTERNS.items():

        # 패턴과 일치하는 모든 문자열 탐색
        for match in pattern.finditer(text):

            detection_value = match.group()

            # 탐지 결과 저장
            detection_results.append(
                {
                    'inquiry_id': inquiry_id,
                    'pii_type': pii_type,
                    'detected_value': detection_value,

                    # 화면 출력용 마스킹 값
                    'masked_preview': (
                        create_masked_value(
                            pii_type=pii_type,
                            detection_value=detection_value,
                        )
                    ),

                    # 원문에서 시작/끝 위치
                    'start_position': match.start(),
                    'end_position': match.end(),
                }
            )

    # 문장 내 등장 순서대로 정렬
    detection_results.sort(key=lambda x: x['start_position'])

    return detection_results


def create_inquiry_summary(
        inquiry_df: pd.DataFrame,
        detection_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    문의별 개인정보 탐지 결과를 요약하여 반환한다.

    생성 컬럼
    ----------
    has_pii
    pii_count
    pii_type
    """

    # 개인정보가 하나도 없는 경우
    if detection_df.empty:

        summary_df = inquiry_df.copy()

        summary_df['has_pii'] = False
        summary_df['pii_count'] = 0
        summary_df['pii_type'] = ""

        return summary_df

    # inquiry_id별 개인정보 개수 및 종류 집계
    detection_summary_df = (
        detection_df
        .groupby('inquiry_id', as_index=False)
        .agg(
            pii_count=('pii_type', 'count'),
            pii_type=(
                'pii_type',
                lambda values: ', '.join(sorted(set(values)))
            )
        )
    )

    # 원본 문의 데이터와 집계 결과 결합
    summary_df = inquiry_df.merge(
        detection_summary_df,
        how='left',
        on='inquiry_id',
        validate='one_to_one'
    )

    # 개인정보가 없는 문의 처리
    summary_df['pii_count'] = summary_df['pii_count'].fillna(0).astype(int)
    summary_df['pii_type'] = summary_df['pii_type'].fillna("")

    # 개인정보 존재 여부(Boolean)
    summary_df['has_pii'] = summary_df['pii_count'] > 0

    return summary_df


def detect_all_inquiries(inquiry_df: pd.DataFrame) -> pd.DataFrame:
    """
    전체 고객 문의 데이터를 순회하면서
    개인정보를 탐지한다.
    """

    all_detection_results = []

    # 문의 한 건씩 검사
    for _, row in inquiry_df.iterrows():

        row_results = detect_pii_from_text(
            inquiry_id=row['inquiry_id'],
            text=row['inquiry_text']
        )

        all_detection_results.extend(row_results)

    detection_columns = [
        'inquiry_id',
        'pii_type',
        'detected_value',
        'masked_preview',
        'start_position',
        'end_position'
    ]

    return pd.DataFrame(
        all_detection_results,
        columns=detection_columns
    )


def main():
    # 입력 데이터 읽기
    inquiry_df = pd.read_csv(
        INPUT_PATH,
        encoding='utf-8-sig'
    )

    print(inquiry_df.head())

    # 개인정보 탐지 수행
    detection_df = detect_all_inquiries(inquiry_df)

    # 문의별 요약 정보 생성
    summary_df = create_inquiry_summary(
        inquiry_df=inquiry_df,
        detection_df=detection_df
    )

    print()
    print(summary_df.head())
    print(summary_df.iloc[0])

    # 출력 폴더가 없으면 생성
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 상세 탐지 결과 저장
    detection_df.to_csv(
        DETECTION_OUTPUT_DIR,
        index=False,
        encoding='utf-8-sig'
    )

    # 문의별 요약 결과 저장
    summary_df.to_csv(
        SUMMARY_OUTPUT_DIR,
        index=False,
        encoding='utf-8-sig'
    )


# 프로그램 시작점
if __name__ == '__main__':
    main()