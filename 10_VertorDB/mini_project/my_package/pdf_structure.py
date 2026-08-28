# csv문서를 gemini 임베딩 모델 기반 벡터문서 만들기
# 라이브러리가 토크나이징과 인덱싱을 자동으로 해줌
import csv, os, json
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import pymupdf


# 기본 디렉토리 정의
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR /"../../.env"
DATA_DIR_PATH = BASE_DIR / "data" / "documents"


# 임베딩 모델 정의
MODEL_NAME = "gemini-embedding-2"
#vector dimension
OUTPUT_DIMENSION = 768 # 최소값


# LLM(Gemini) 연동
load_dotenv(dotenv_path=ENV_PATH)
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY를 읽을 수 없습니다."
    )

if not DATA_DIR_PATH.exists():
    raise FileNotFoundError(
        f"파일 데이터를을 찾을 수 없습니다: {DATA_DIR_PATH}"
    )

client = genai.Client(
    api_key=api_key
)

# 디버깅용 출력함수
def print_title(title:str):
    print('\n' + '-' * 80)
    print(title)
    print('-' * 80)
    print()

def extract_pdf_pages(pdf_path: Path) -> pd.DataFrame:
    # PDF 파일이 존재하지 않으면 예외 발생
    if not pdf_path.exists():
        raise FileNotFoundError(f'pdf 파일을 찾을 수 없습니다.: {pdf_path}')

    # PDF 파일 읽기
    # reader = PdfReader(str(pdf_path))
    reader = pymupdf.open(pdf_path)
    # 페이지별 정보를 저장할 리스트
    page_readers = []

    # 모든 페이지를 순회하면서 텍스트 추출
    for page_number, page in enumerate(reader, start=1):

        # 텍스트 추출 (추출 실패 시 빈 문자열 사용)
        # page_text = page.extract_text() or ""
        # # 앞뒤 공백 제거
        # page_text = page_text.strip()
        page_text = page.get_text("text").strip()

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


# 데이터 파일 로드
def load_document(data_path: Path) -> list[dict]:
    # 파일 디렉토리 목록 추출
    print(os.listdir(data_path))

    for file_name in os.listdir(data_path):
        # 확장자 추출
        extension = Path(file_name).suffix
        print_title(file_name)
        
        file_dir = data_path / file_name

        if extension == '.csv' :
            with file_dir.open(
                mode='r',
                encoding='utf-8-sig',
                newline=''
            )as file:
                csv_dict = csv.DictReader(file)
                return list(csv_dict)
        
        elif extension == '.json' :
            with file_dir.open(
                mode='r',
                encoding='utf-8-sig',
            )as file:
                file_dict = json.load(file)
                return list(file_dict)
        
        elif extension == '.pdf' : # 데이터프레임 반환
            pdf_dict = pdf_df.to_dict(extract_pdf_pages(file_dir), orient='records')
            return list(pdf_dict)

        else :
            print("허용되지 않은 확장자입니다.")
            return 

documents = load_document(DATA_DIR_PATH)
print(type(documents))
print(f'사용할 문서(라인) 수: {len(documents)}')
print(f'첫 문서: {documents[0]}')







