import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import SystemMessage, HumanMessage

MODEL_NAME = "gemini-3.7-flash"
model = ChatGoogleGenerativeAI(model=MODEL_NAME, api_key=api_key)

system_message = SystemMessage(content=(
    "당신은 스마트팜 현장 교육 담당자입니다. "
    "어려운 전문 용어를 바로 사용하지 말고 먼저 쉬운 현장 예시를 들어 설명하세요. "
    "답변은 5문장 이내로 작성하세요."
))
human_message = HumanMessage(
    content="관수 펌프 압력이 낮아질 때 무엇을 먼저 확인해야 하나요?"
)
messages = [system_message, human_message]
response = model.invoke(messages)

print("=" * 80)
print("messages response")
print("=" * 80)
print(response.text)
