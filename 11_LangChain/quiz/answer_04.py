import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

MODEL_NAME = "gemini-3.7-flash"
model = ChatGoogleGenerativeAI(model=MODEL_NAME, api_key=api_key)

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "당신은 스마트팜 설비 교육 강사입니다. "
        "학습자 수준은 {learner_level}입니다. "
        "{equipment} 설비를 학습자 수준에 맞게 설명하세요."
    )),
    ("human", (
        "현재 증상은 '{symptom}'입니다. "
        "우선 확인할 항목을 {answer_count}개 알려주세요."
    )),
])

inputs = [
    {
        "learner_level": "초보자",
        "equipment": "관수 펌프",
        "symptom": "운전 중 압력이 평소보다 낮다",
        "answer_count": 3,
    },
    {
        "learner_level": "중급자",
        "equipment": "IoT 게이트웨이",
        "symptom": "데이터가 일정 간격으로 누락된다",
        "answer_count": 4,
    },
]

for number, input_data in enumerate(inputs, start=1):
    prompt_value = prompt.invoke(input_data)
    print("\n" + "=" * 80)
    print(f"입력 {number}")
    print("=" * 80)
    for index, message in enumerate(prompt_value.messages, start=1):
        print(f"\n[{index}] {type(message).__name__}")
        print(message.text if hasattr(message, "text") else message.content)
    response = model.invoke(prompt_value)
    print("\n모델 답변")
    print(response.text)
