import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

from langchain_google_genai import ChatGoogleGenerativeAI

MODEL_NAME = "gemini-3.7-flash"
model = ChatGoogleGenerativeAI(model=MODEL_NAME, api_key=api_key)

question = (
    "스마트팜에서 EC와 pH를 함께 관리해야 하는 이유를 "
    "초보자에게 4문장으로 설명해 주세요."
)
response = model.invoke(question)

print("=" * 80)
print("응답 본문")
print("=" * 80)
print(response.text)
print("\n응답 객체 타입")
print(type(response))
print("\nresponse_metadata")
print(response.response_metadata)
print("\nusage_metadata")
print(response.usage_metadata)
