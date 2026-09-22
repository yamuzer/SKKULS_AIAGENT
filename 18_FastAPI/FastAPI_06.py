import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, status
from pydantic import BaseModel

app = FastAPI()

UPLOAD_DIR = Path('uploads')

UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    '.txt',
    '.csv',
    '.pdf',
    '.png',
    '.jpg',
    '.jpeg'
}

MAX_FILE_SIZE = 10 * 1024 * 1024

class FileUploadResponse(BaseModel):

    filename: str

    content_type: str | None

    size: int


class FileSaveResponse(BaseModel):

    original_filename: str

    saved_filename: str

    saved_path: str

    content_type: str | None


@app.get('/')
def root():
    return {
        'message':'root~~~'
    }


@app.post(
    '/files/info', 
    response_model=FileUploadResponse
)
def get_file_info(
    file: UploadFile
):

    file.file.seek(0, 2)

    # 파일 전체 크기
    size = file.file.tell()


    file.file.seek(0)


    return {
        'filename': file.filename or '',
        'content_type': file.content_type,
        'size': size
    }   


@app.post('/files/text')
def read_text_file(
    file:UploadFile
):

    safe_name = Path(file.filename or 'uploaded.txt').name

    extension = Path(safe_name).suffix.lower()

    if extension != '.txt':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='TXT 파일만 업로드할 수 있습니다.'
        )


    contents = file.file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail='파일 크기는 10MB 이하여야 합니다.'
        )

    try:
        text = contents.decode('utf-8-sig')

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='UTF-8 또는 UTF-8-SIG 텍스트 파일이 필요합니다.'
        )

    preview = text[:300]

    return {
        'file_name': safe_name,
        'characters': len(text),
        'preview': preview
    }


@app.post(
    '/files/save',
    response_model=FileSaveResponse,
    status_code=status.HTTP_201_CREATED
)
def save_file(
    file: UploadFile
):
    safe_name = Path(file.filename or 'uploaded_file').name

    extension = Path(safe_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'message': '허용하지 않은 파일 형식입니다.',
                'allowed_extensions': sorted(ALLOWED_EXTENSIONS)
            }
        )

    destination = UPLOAD_DIR / safe_name

    with destination.open(
        'wb'
    )as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )


    return {
        'original_filename': file.filename or '',
        'saved_filename': safe_name,
        'saved_path': str(destination),
        'content_type': file.content_type
    }


@app.post('/files/multiple')
def upload_multiple_files(
    files: list[UploadFile]
):

    result = []

    for file in files:
        safe_name = Path(file.filename or 'uploaded_file').name
        file.file.seek(0, 2)
        size = file.file.tell()

        file.file.seek(0)

        result.append(
            {
                'filename': safe_name,
                'content_type': file.content_type,
                'size': size
            }
        )

    return {
        'count': len(result),
        'files': result
    }
    

    