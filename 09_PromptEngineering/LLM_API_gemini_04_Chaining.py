import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError('GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.')


client = genai.Client(api_key=api_key)

def ask_gemini(prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt
    )
    return interaction.output_text

customer_message = """
지난주 월요일에 노트북을 주문했습니다.
원래 금요일까지 배송된다고 했는데 아직 상품을 받지 못했습니다.
택배 조회를 해보니 3일동안 물류센터에서 이동하지 않고 있습니다.
이 노트북은 다음 주 월요일 회사 발표에 사용해야 해서 반드시 필요합니다.
오늘 안에 배송 여부를 확실히 알 수 없다면 주문을 취소하고 전액 환불받고 싶습니다.
주문 번호는 ORD-2026-0813-1057 입니다.
"""

prompt_step1 = f"""
다음 고객 문의에서 객관적으로 확인할 수 있는 핵심 정보만 추출하라.
[고객 문의]
{customer_message}
___
다음 항목으로 정리하라.
- 주문번호 : 
- 상품 : 
- 발생한 문제 : 
- 배송 상태 : 
- 고객이 언급한 일정 :
- 현재 고객 요구 :
- 환불 요구 여부 
주의 : 
고객 문의에서 확인할 수 없는 내용은 추측하지 않는다.
"""

step1_result = ask_gemini(prompt=prompt_step1)
print('\nstep1')
print(step1_result)

prompt_step2 = f"""
다음은 고객 문의에서 추출한 핵심 정보다.
[이전 단계 결과]
{step1_result}
이 정보를 바탕으로 고객 문의를 분석하라.
문의 유형은 다음 중 하나를 선택한다.
- 배송
- 환불
- 제품 불량
- 결제
- 회원 정보

긴급도는 다음 중 하나를 선택한다.
- 낮음
- 보통
- 높음

판단 시 다음을 확인한다.
1. 현재 발생한 핵심 문제
2. 고객의 최종 요구
3. 고객이 언급한 시간 제약
4. 업무상 긴급하게 처리할 필요가 있는지

다음 형식으로 작성하라.
핵심 문제:
고객 최종 요구:
문의 유형:
긴급도:
판단 근거:
"""
step2_result = ask_gemini(prompt=prompt_step2)
print('\nstep2')
print(step2_result)

prompt_step3 = f"""
다음은 고객 문의 분석 결과다.
[고객 정보 추출 결과]
{step1_result}
[문의 분석 결과]
{step2_result}

위 정보를 이용하여 고객지원 담당자가 취해야할 대응 방향을 작성하라.

다음 원칙을 따른다.
- 확인되지 않은 배송 상태를 만들어내지 않는다.
- 실제 환불 완료 여부를 만들어내지 않는다.
- 고객이 요청한 내용과 긴급도를 반영한다.
- 먼저 확인해야 할 업무와 그 이후 가능한 조치를 구분한다.

다음 형식으로 작성하라.

우선 확인 사항:
1.
2.

고객에게 안내할 내용:
1.
2.

가능한 후속 조치:
1.
2.
"""

print('\nstep3')
print(step3_result)
