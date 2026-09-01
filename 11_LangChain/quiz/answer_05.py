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
        "당신은 계절별 스마트팜 운영을 안내하는 현장 관리자입니다. "
        "현재 계절은 {season}이고 관리 주제는 {topic}입니다."
    )),
    ("human", "{question}"),
])

chain = prompt | model
input_data = {
    "season": "여름",
    "topic": "온실 환경 관리",
    "question": "온도는 높고 습도도 높은 상황에서 점검 순서를 알려주세요.",
}
response = chain.invoke(input_data)
print("chain type:", type(chain))
print("\n응답")
print(response.text)
