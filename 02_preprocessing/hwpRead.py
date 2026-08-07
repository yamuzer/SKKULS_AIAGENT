import pathlib
from pathlib import Path
import shutil
import tempfile

import pandas as pd
import pythoncom
import win32com.client as win32

# 현재 실행 중인 파이썬 파일의 위치를 기준으로 경로 설정
BASE_DIR = Path(__file__).resolve().parent

# 입력 HWP/HWPX 파일 경로
INPUT_PATH = BASE_DIR / 'data' / 'public_sample.hwpx'

# 출력 폴더 및 CSV 저장 경로
OUTPUT_DIR = BASE_DIR / 'output'
OUTPUT_CSV_PATH = OUTPUT_DIR / 'hwp_paragraphs.csv'


def detect_file_format(file_path: Path) -> str:
    """
    파일의 시그니처(Magic Number)를 확인하여
    실제 파일 형식을 판별한다.
    """

    # 파일 존재 여부 확인
    if not file_path.exists():
        raise FileNotFoundError(f'File not found: {file_path}')

    # 빈 파일인지 확인
    if file_path.stat().st_size == 0:
        raise ValueError('파일 크기가 0바이트입니다.')

    # 파일 앞 8바이트 읽기
    signature = file_path.read_bytes()[:8]

    # ZIP 기반 포맷(HWPX)의 시그니처
    if signature.startswith(b'PK'):
        return "HWPX"

    # OLE Compound File(HWP)의 시그니처
    hwp_signature = bytes.fromhex("D0 CF 11 E0 A1 B1 1A E1")

    if signature == hwp_signature:
        return "HWP"

    # 알 수 없는 형식
    return "UNKNOWN"


def extract_hwp_text(file_path: Path) -> list[str]:
    """
    Windows에 설치된 한글(HWP)의 COM 자동화를 이용하여
    문서의 텍스트를 추출한 뒤 문단 단위 리스트로 반환한다.
    """

    # COM 객체 사용을 위한 초기화
    pythoncom.CoInitialize()

    hwp = None
    temporary_directory = None
    temporary_hwp_path = None

    try:
        # ------------------------------------------------------------------
        # 원본 파일을 임시 폴더로 복사
        # 일부 환경에서는 원본 대신 임시 파일을 여는 것이 안정적이다.
        # ------------------------------------------------------------------
        temporary_directory = tempfile.TemporaryDirectory()
        temporary_hwp_path = Path(temporary_directory.name) / "public_sample.hwp"

        shutil.copy2(file_path, temporary_hwp_path)

        # 한글(HWP) COM 객체 생성
        hwp = win32.gencache.EnsureDispatch("HWPFrame.HWPObject")

        # 한글 프로그램 창 표시
        hwp.XHwpWindows.Item(0).Visible = True

        # 보안 모듈 등록
        # 환경에 따라 실패할 수 있으므로 예외는 무시
        try:
            hwp.RegisterModule(
                "FilePathCheckDLL",
                "FilePathCheckerModule"
            )
        except Exception:
            pass

        # 문서 열기
        open_result = hwp.Open(str(temporary_hwp_path))

        if not open_result:
            raise RuntimeError('한글 프로그램에서 문서를 열지 못했습니다.')

        # ----------------------------------------------------------
        # InitScan()
        #
        # 첫 번째 인자(0x00)
        #   일반적인 텍스트 검색
        #
        # 두 번째 인자(0x0077)
        #   본문뿐 아니라 표, 글상자 등 여러 컨트롤 내부의
        #   텍스트까지 포함하여 검색
        # ----------------------------------------------------------
        hwp.InitScan(
            0x000F, # 표에 있는 데이터까지.
            0x0077,
            0,
            0,
            -1,
            -1
        )

        # 추출된 텍스트 조각 저장
        text_chunks = []

        while True:
            # 문서에서 다음 텍스트 블록 읽기
            state, text = hwp.GetText()

            # state
            # 0 : 텍스트 없음
            # 1 : 문서 끝(EOF)
            if state <= 1:
                break

            if text:
                text_chunks.append(text)

        # 스캔 종료
        hwp.ReleaseScan()

        # 하나의 문자열로 결합
        full_text = "".join(text_chunks)

        # 줄바꿈 형식 통일
        full_text = full_text.replace('\r\n', '\n').replace('\r', '\n')

        paragraphs = []

        # 빈 줄 제거 후 문단 리스트 생성
        for line in full_text.split('\n'):
            cleaned_line = line.strip()
            if cleaned_line:
                paragraphs.append(cleaned_line)

        return paragraphs

    finally:
        # ----------------------------------------------------------
        # COM 객체 및 임시 리소스 정리
        # ----------------------------------------------------------
        if hwp is not None:
            # 열린 문서 닫기
            try:
                hwp.Clear(1)
            except Exception:
                pass

            # 한글 프로그램 종료
            try:
                hwp.Quit()
            except Exception:
                pass

        # 임시 폴더 삭제
        if temporary_directory is not None:
            temporary_directory.cleanup()

        # COM 종료
        pythoncom.CoUninitialize()


def create_paragraph_dataframe(paragraphs: list[str]) -> pd.DataFrame:
    records = []
    for paragraph_number, paragraph_text in enumerate(paragraphs, start=1):
        records.append(
            {
                'paragraph_number': paragraph_number,
                'paragraph_text': paragraph_text,
                'character_count': len(paragraph_text),
            }
        )
    return pd.DataFrame(records)



def main():
    try:
        # 실제 파일 형식 확인
        actual_format = detect_file_format(INPUT_PATH)

        print(f'파일 확장자: {INPUT_PATH.suffix}')
        print(f'실제 파일 형식: {actual_format}')

        # 문단 단위 텍스트 추출
        paragraphs = extract_hwp_text(INPUT_PATH)

    except FileNotFoundError as error:
        print('[file error]')
        print(error)
        return

    # 추출 결과가 없는 경우
    if not paragraphs:
        print('추출된 텍스트가 없습니다.')
        return

    # 결과 출력
    print(paragraphs)

    paragraphs_df = create_paragraph_dataframe(paragraphs)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paragraphs_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8')

# 프로그램 시작점
if __name__ == '__main__':
    main()

# pywintypes.com_error: (-2147221005, '잘못된 클래스 문자열입니다.', None, None)
## COM 객체를 생성할 때 해당 COM 클래스(ProgID)를 Windows가 찾지 못했다는 의미
## 한글(Hancom Office)이 설치되어 있지 않음, 한글뷰어와 공공한글 불가.