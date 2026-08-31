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

system_message = SystemMessage(
    content=(
    '당신은 python과 AI를 가르치는 강사입니다.'
    '이 대화 안에서 사용자가 알려준 정보를 기억해서 다음 질문에 활용하세요.'
    '답변은 5문장 이내로 작성하세요.'
    )
)

messages = [
    system_message
]

first_question = (
    "오늘 내가 복습할 주제는 '벡터 데이터베이스'야."
)

first_human_message = HumanMessage(
    content=first_question
)

messages.append(first_human_message)

first_response = model.invoke(messages)
print(first_response.text)

messages.append(first_response) # ai message
print_title('messages ')
print(messages)

second_question=(
    '내가 오늘 복습하기로 한 주제가 뭐였지?'
)

secon_human_message = HumanMessage(
    content=second_question
)

messages.append(secon_human_message)

history_response = model.invoke(messages)
print_title('history response')
print(history_response.text)


for index, message in enumerate(messages, start=1):
    print(f'\n{[index]}')
    print(f'message type:{type(message).__name__}')

    if hasattr(message, 'text'):
        print(message.text)
    else:
        print(message.content)




# print(system_message.content)
# print()
# print(first_human_message.content)


# # messages= [
# #     system_message,
# #     first_human_message # or AIMessage
# # ]

# message_response = model.invoke(messages)
# print_title('messages response')
# print(message_response.text)