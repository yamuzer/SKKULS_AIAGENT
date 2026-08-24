# """
# ------------------------------------------------------------
# 문제1. Interaction 객체와 내부 구조 확인
# ------------------------------------------------------------
# 문제:
# 다음 질문을 Gemini에게 전달한다.

# "데이터 분석에서 이상치(outlier)가
# 평균과 중앙값에 어떤 영향을 줄 수 있는지
# 간단한 숫자 예시를 포함해서 설명해줘."

# 다음을 출력한다.

# 1. interaction.output_text
# 2. type(interaction)
# 3. interaction.id
# 4. interaction.model
# 5. interaction.status
# 6. interaction.created
# 7. interaction.updated
# 8. interaction.steps 개수
# 9. 각 step의 type
# 10. 각 step의 model_dump(exclude_none=True)
# 11. Input / Output / Thought / Total Token

# 추가:
# model_output 단계의 content 중
# type이 text인 실제 텍스트를 직접 찾아 출력한다.
# """


import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError('GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.')

client = genai.Client(
    api_key = api_key
)
# print(client)

prompt1 = """
데이터 분석에서 이상치(outlier)가
평균과 중앙값에 어떤 영향을 줄 수 있는지
간단한 숫자 예시를 포함해서 설명해줘.
"""
def print_title(title: str) -> None:
    print('='*100)
    print(f'\n{title}')
    print('='*100)

def ask_gemini(prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt
    )
    return interaction.output_text

def ask_gemini_full(prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        input=prompt
    )
    return interaction

# print_title('\n1. interaction.output_text')
# answer1 = ask_gemini(prompt1)
# print(answer1)

# print_title('\n2. type(interaction)')
# instance = ask_gemini_full(prompt1)
# print(type(instance))

# print_title('\n3. interaction.id')
# print(instance.id)

# print_title('\n4. interaction.model')
# print(instance.model)

# print_title('\n5. interaction.status')
# print(instance.status)

# print_title('\n6. interaction.created')
# print(instance.created)

# print_title('\n7. interaction.updated')
# print(instance.updated)

# print_title('\n8. interaction.steps 개수')
# print(len(instance.steps)) # 1. 사용자 질문 입력  2. 모델 답변 출력

# print_title('\n9. 각 step의 type')
# print(type(instance.steps[0]))
# print(type(instance.steps[1]))

# print_title('\n10. 각 step의 model_dump(exclude_none=True)')
# # 실행 단계 객체의 데이터 중 값이 없는 필드(None)를 제외하고 실제 데이터가 있는 핵심 정보만 딕셔너리(Dict) 형태로 추출
# print(instance.steps[0].model_dump(exclude_none=True))
# print(instance.steps[1].model_dump(exclude_none=True))

# print_title('\n11. Input / Output / Thought / Total Token')
# if instance.usage: # 소비된 토큰의 세부 통계
#     print(f'input tokens: {instance.usage.total_input_tokens}')
#     print(f'output tokens: {instance.usage.total_output_tokens}')
#     print(f'thought tokens: {instance.usage.total_thought_tokens}')
#     print(f'total tokens: {instance.usage.total_tokens}')

# print_title('\n # model_output 단계의 content 중 type이 text인 실제 텍스트를 직접 찾아 출력한다.')
# print(instance.steps[1].model_dump(exclude_none=True)['content'][0]['text'])


# ------------------------------------------------------------
# 문제2. Gemini 호출 함수 만들기
# ------------------------------------------------------------
# 목표:
# 반복되는 API 호출 코드를 함수로 정리한다.

# 함수:
# ask_gemini(prompt: str) -> str

# 요구사항:
# 1. 함수 내부에서 client.interactions.create() 실행
# 2. 최종 output_text를 반환
# 3. 다음 세 질문을 함수로 각각 실행

# - "정밀도와 재현율의 차이를 설명해줘."
# - "과적합과 과소적합의 차이를 설명해줘."
# - "훈련 데이터와 검증 데이터의 역할 차이를 설명해줘."

# 4. 각 결과 앞에 질문 번호를 출력한다.

# 추가:
# ask_gemini_with_usage() 함수를 하나 더 만들어
# 답변과 Total Token을 함께 반환한다.

# print_title('세 질문을 함수로 각각 실행')
prompt2 = ["정밀도와 재현율의 차이를 설명해줘.", "과적합과 과소적합의 차이를 설명해줘.", "훈련 데이터와 검증 데이터의 역할 차이를 설명해줘."]
# for i in range(len(prompt2)):
#     result = ask_gemini(prompt2[i])
#     print(f'[{i+1}]\n{result}')
#     print('')

print_title('추가')
def ask_gemini_with_usage(prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        input=prompt
    )
    return interaction.output_text, interaction.usage

# for i in range(len(prompt2)):
#     result, usage = ask_gemini_with_usage(prompt2[i])
#     print(f'[{i+1}]프롬프트의 응답\n{result}')
#     print(f'[{i+1}]프롬프트의 토탈 토큰\n{usage.total_tokens}')
#     print('')




# ------------------------------------------------------------
# 문제3. previous_interaction_id로 4단계 대화
# ------------------------------------------------------------
# 첫 질문:
# "다음 학습 계획을 기억해줘.
# 수강생 이름은 박서준이고,
# 현재 SQL을 공부하고 있으며,
# 다음 학습 목표는 Python 데이터 분석이고,
# 하루 학습 가능 시간은 2시간이야."

# 두 번째 질문:
# "현재 공부하고 있다고 말한 과목은?"

# 세 번째 질문:
# "다음 학습 목표는 무엇이라고 했지?"

# 네 번째 질문:
# "앞의 정보를 기준으로 하루 2시간짜리 학습 순서를 4단계로 제안해줘."

# 조건:
# - 2번은 interaction_1.id에 연결
# - 3번은 interaction_2.id에 연결
# - 4번은 interaction_3.id에 연결
# - 마지막에 네 개 id를 모두 출력

prompt3_1 = """
다음 학습 계획을 기억해줘.
수강생 이름은 박서준이고,
현재 SQL을 공부하고 있으며,
다음 학습 목표는 Python 데이터 분석이고,
하루 학습 가능 시간은 2시간이야.
"""
prompt3_2 = """
현재 공부하고 있다고 말한 과목은?
"""
prompt3_3 = """
다음 학습 목표는 무엇이라고 했지?
"""
prompt3_4 = """
앞의 정보를 기준으로 하루 2시간짜리 학습 순서를 4단계로 제안해줘
"""
def ask_gemini_send_id(
    previous_id,
    prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        input=prompt,
        previous_interaction_id=previous_id
    )
    return interaction

print_title('첫 번째 대화')
interaction1 = ask_gemini_full(prompt=prompt3_1)
print(interaction1.output_text)

print_title('두 번째 대화')
interaction2 = ask_gemini_send_id(
    previous_id=interaction1.id,
    prompt=prompt3_2)
print(interaction2.output_text)

print_title('세 번째 대화')
interaction3 = ask_gemini_send_id(
    previous_id=interaction2.id,
    prompt=prompt3_3)
print(interaction3.output_text)

print_title('네 번째 대화')
interaction4 = ask_gemini_send_id(
    previous_id=interaction3.id,
    prompt=prompt3_4)
print(interaction4.output_text)

print_title('ID 네개 모두 출력')
print(interaction1.id, interaction2.id, interaction3.id, interaction4.id)


# ------------------------------------------------------------
# 문제4. 일반 Prompt와 CO-STAR Prompt 비교
# ------------------------------------------------------------
# 상황:

# 한 교육센터의 최근 변화:
# - 수강생 수: 95명 → 148명
# - 질문 대기시간: 6분 → 16분
# - 장비 장애 신고: 월 5건 → 14건
# - 과제 미제출률: 7% → 13%
# - 만족도: 4.7점 → 4.0점

# 문제:
# A. 일반 Prompt
# B. CO-STAR Prompt

# 두 개를 만들어 같은 데이터로 실행한다.

# CO-STAR 조건:
# C: 교육센터의 최근 운영 변화
# O: 가장 시급한 문제와 우선 조치를 판단
# S: 운영 보고서
# T: 객관적, 과장 금지
# A: 센터장
# R:
# [핵심 지표]
# [가장 시급한 문제]
# [근거]
# [우선 조치 2개]
# [3문장 요약]

# 마지막에 두 응답을 모두 출력한다.
