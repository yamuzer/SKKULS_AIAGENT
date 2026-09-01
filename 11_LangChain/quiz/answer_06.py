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
from langchain_core.output_parsers import StrOutputParser

MODEL_NAME = "gemini-3.7-flash"
model = ChatGoogleGenerativeAI(model=MODEL_NAME, api_key=api_key)
parser = StrOutputParser()

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "당신은 스마트팜 점검 교육 담당자입니다. "
        "사용자의 역할은 {role}입니다. "
        "{equipment} 점검 내용을 이해하기 쉽게 설명하세요."
    )),
    ("human", "{request}"),
])

input_data = {
    "role": "신입 스마트팜 관리자",
    "equipment": "pH 센서",
    "request": "교정 직후 측정값이 흔들릴 때 확인할 사항 3개",
}

message_chain = prompt | model
message_response = message_chain.invoke(input_data)
print("prompt | model 반환 타입:", type(message_response))
print(message_response.text)

string_result = parser.invoke(message_response)
print("\nparser 별도 실행 반환 타입:", type(string_result))
print(string_result)

string_chain = prompt | model | parser
final_result = string_chain.invoke(input_data)
print("\nprompt | model | parser 반환 타입:", type(final_result))
print(final_result)
