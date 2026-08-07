from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------
# 경로 설정
# ------------------------------------------------------------------

# 현재 실행 중인 파일의 위치
BASE_DIR = Path(__file__).resolve().parent

# 데이터 및 출력 폴더
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'

# 입력 파일
INQUIRY_PATH = DATA_DIR / 'customer_inquiries_clean.csv'
COUNTRY_MAPPING_PATH = DATA_DIR / 'country_mapping.csv'
LANGUAGE_MAPPING_PATH = DATA_DIR / 'language_mapping.csv'

# 출력 파일
OUTPUT_PATH = OUTPUT_DIR / 'customer_inquiries_standardized.csv'
UNMATCHED_PATH = OUTPUT_DIR / 'unmatched_country_language.csv'


def load_data():
    """
    입력 데이터와 국가/언어 기준정보를 읽어온다.
    """

    inquiry_df = pd.read_csv(INQUIRY_PATH, encoding='utf-8-sig')
    country_mapping_df = pd.read_csv(COUNTRY_MAPPING_PATH, encoding='utf-8-sig')
    language_mapping_df = pd.read_csv(LANGUAGE_MAPPING_PATH, encoding='utf-8-sig')

    return inquiry_df, country_mapping_df, language_mapping_df


def standardize_country(
    inquiry_df: pd.DataFrame,
    country_mapping_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    국가명을 기준정보와 매핑하여 표준 국가코드를 추가한다.
    """

    result_df = inquiry_df.merge(
        country_mapping_df,
        how='left',
        left_on='country',
        right_on='country_raw',
    )

    return result_df


def standardize_language(
    inquiry_df: pd.DataFrame,
    language_mapping_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    언어명을 기준정보와 매핑하여 표준 언어코드를 추가한다.
    """

    result_df = inquiry_df.merge(
        language_mapping_df,
        how='left',
        left_on='language',
        right_on='language_raw',
    )

    return result_df


def add_mapping_status(inquiry_df: pd.DataFrame) -> pd.DataFrame:
    """
    국가 및 언어 매핑 결과를 상태 컬럼으로 추가한다.

    country_mapping_status
        MATCHED / UNMATCHED

    language_mapping_status
        MATCHED / UNMATCHED

    mapping_status
        국가와 언어가 모두 매핑되면 MATCHED,
        하나라도 실패하면 CHECK
    """

    # 국가 매핑 여부
    inquiry_df['country_mapping_status'] = (
        inquiry_df['country_code_2']
        .notna()
        .map({
            True: 'MATCHED',
            False: 'UNMATCHED'
        })
    )

    # 언어 매핑 여부
    inquiry_df['language_mapping_status'] = (
        inquiry_df['language_code']
        .notna()
        .map({
            True: 'MATCHED',
            False: 'UNMATCHED'
        })
    )

    # 국가와 언어가 모두 매핑되었는지 확인
    inquiry_df['mapping_status'] = (
        inquiry_df[
            ['country_mapping_status', 'language_mapping_status']
        ]
        .eq('MATCHED')
        .all(axis=1)
        .map({
            True: 'MATCHED',
            False: 'CHECK'
        })
    )

    return inquiry_df


def main() -> None:
    # 입력 데이터 읽기
    inquiry_df, country_mapping_df, language_mapping_df = load_data()

    print(f'전체 문의 건수: {len(inquiry_df)}')
    print(f'국가 기준정보 건수: {len(country_mapping_df)}')
    print(f'언어 기준정보 건수: {len(language_mapping_df)}')

    # 국가 표준화
    standardized_df = standardize_country(
        inquiry_df=inquiry_df,
        country_mapping_df=country_mapping_df
    )

    # 언어 표준화
    standardized_df = standardize_language(
        inquiry_df=standardized_df,
        language_mapping_df=language_mapping_df
    )

    # 매핑 상태 컬럼 추가
    standardized_df = add_mapping_status(standardized_df)

    # 기준정보 컬럼 제거
    standardized_df = standardized_df.drop(
        columns=['country_raw', 'language_raw']
    )

    # 매핑 실패 데이터 추출
    unmatched_df = standardized_df[
        standardized_df['mapping_status'] == 'CHECK'
    ].copy()

    print('=' * 80)
    print('매핑 결과')
    print('=' * 80)

    print(f"국가 매핑 성공: {int(standardized_df['country_code_2'].notna().sum())}건")
    print(f"언어 매핑 성공: {int(standardized_df['language_code'].notna().sum())}건")

    # 출력 폴더 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 전체 결과 저장
    standardized_df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding='utf-8-sig',
    )

    # 매핑 실패 데이터 저장
    unmatched_df.to_csv(
        UNMATCHED_PATH,
        index=False,
        encoding='utf-8-sig',
    )


# 프로그램 시작점
if __name__ == '__main__':
    main()