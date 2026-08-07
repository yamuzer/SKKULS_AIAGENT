from pathlib import Path
import pandas as pd
from pypdf import PdfReader

# 현재 파이썬 파일이 위치한 디렉터리
# 현재 실행 중인 파이썬 파일의 경로를 저장하고 있는 특별한(내장) 변수, path 객체 반환
BASE_DIR = Path(__file__).resolve().parent
print(__file__)


# 입력 PDF 파일 경로
PDF_PATH = BASE_DIR / "data" / "global_customer_support_report.pdf"
# 추출 결과를 저장할 CSV 파일 경로
OUTPUT_PATH = BASE_DIR / "data" / "pdf_page_text.csv"
# pathlib.Path 객체가 / 연산자를 오버로딩(overloading)한 것
# 이게 가능한 이유는 BASE_DIR가 문자열(str)이 아니라 Path 객체이기 때문

def extract_pdf_pages(pdf_path: Path) -> pd.DataFrame:
    """
    PDF 파일의 모든 페이지에서 텍스트를 추출하여 DataFrame으로 반환한다.

    Returns
    -------
    file_name       : 원본 PDF 파일명
    page_number     : PDF 페이지 번호
    page_text       : 해당 페이지에서 추출한 텍스트
    character_count : 추출된 문자 수
    """

    # PDF 파일이 존재하지 않으면 예외 발생
    if not pdf_path.exists():
        raise FileNotFoundError(f'pdf 파일을 찾을 수 없습니다.: {pdf_path}')

    # PDF 파일 읽기
    reader = PdfReader(str(pdf_path))

    # 페이지별 정보를 저장할 리스트
    page_readers = []

    # 모든 페이지를 순회하면서 텍스트 추출
    for page_number, page in enumerate(reader.pages, start=1):

        # 텍스트 추출 (추출 실패 시 빈 문자열 사용)
        page_text = page.extract_text() or ""

        # 앞뒤 공백 제거
        page_text = page_text.strip()

        # 페이지 정보를 딕셔너리 형태로 저장
        page_readers.append(
            {
                'file_name': pdf_path.name,          # PDF 파일명
                'page_number': page_number,          # 페이지 번호
                'page_text': page_text,              # 추출된 텍스트
                'character_count': len(page_text),   # 문자 수
            }
        )

    # 리스트를 DataFrame으로 변환하여 반환
    return pd.DataFrame(page_readers)


def main():
    # PDF에서 페이지별 텍스트 추출
    pdf_df = extract_pdf_pages(PDF_PATH)

    # 전체 페이지 수 출력
    print(f'전체 페이지 수: {len(pdf_df)}')
    print()

    # 페이지별 추출 결과 출력
    for row in pdf_df.itertuples(index=False):
        print('-' * 70)
        print(f'{row.page_number}페이지')
        print(f'추출 문자 수: {row.character_count}')
        print('-' * 70)
        print(row.page_text)
        print(end='\n\n')

    # 출력 폴더가 없으면 생성
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # DataFrame을 CSV 파일로 저장
    pdf_df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8')

    # 저장 완료 메시지 출력
    print('=' * 80)
    print(f'csv 저장 완료: {OUTPUT_PATH}')


# 현재 파일을 직접 실행했을 때만 main() 함수 실행
if __name__ == "__main__":
    main()