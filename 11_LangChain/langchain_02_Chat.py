import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage, SystemMessage

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

MODEL_NAME=('gemini-3.7-flash')

model = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    api_key=api_key
)

def print_title(title:str)-> None:
    print('\n'+'='*80)
    print(title)
    print('='*80)
    print()

question = 'RAG에서 Chunking이 왜 필요한지 설명해주세요.'

'''
print_title('1. only question')
plain_response = model.invoke(question)
print(plain_response.text)
'''

system_message = SystemMessage(
    content=(
    '당신은 python과 AI를 가르치는 강사입니다.'
    '어려운 용어를 먼저 사용하지 말고 쉬운 비유를 사용하세요.'
    '답변은 5문장 이내로 작성하세요.'
    )
)

human_message = HumanMessage(
    content=question
)
print(system_message.content)
print()
print(human_message.content)

messages= [
    system_message,
    human_message
]

message_response = model.invoke(messages)
print_title('messages response')
print(message_response.text)