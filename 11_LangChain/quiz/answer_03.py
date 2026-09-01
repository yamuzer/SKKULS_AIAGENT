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

messages = [
    SystemMessage(content=(
        "당신은 스마트팜 설비 점검 교육 도우미입니다. "
        "이 대화에서 사용자가 알려준 정보를 기억해 다음 질문에 활용하세요. "
        "답변은 간결하게 작성하세요."
    ))
]
questions = [
    "이번 점검에서 내가 우선 확인할 설비는 LED 보광등이야. 기억해줘.",
    "내가 우선 확인하기로 한 설비가 뭐였지?",
    "그 설비를 점검할 때 초보자가 확인하기 쉬운 항목 2개만 알려줘.",
]

for question in questions:
    human = HumanMessage(content=question)
    messages.append(human)
    response = model.invoke(messages)
    messages.append(response)
    print("\n질문:", question)
    print("응답:", response.text)

print("\n" + "=" * 80)
print("전체 대화 이력")
print("=" * 80)
for index, message in enumerate(messages, start=1):
    print(f"\n[{index}] {type(message).__name__}")
    print(message.text if hasattr(message, "text") else message.content)
