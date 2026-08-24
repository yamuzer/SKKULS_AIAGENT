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

# CO-STAR
# Conatext : 어떤 상황
# Objective : 무엇을 달성할 것인지
# Style : 어떤 작성 스타일로
# Tone : 어떤 말투와 분위기
# Audience : 누구에 전달할 것인지
# Response : 어떤 결과 형태로 받을 것인지





def ask_gemini(
    prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt
    )
    return interaction.output_text

business_data = """
최근 2개월 동안 다음과 같은 변화가 발생했다.

평균 배송기간: 1.9일 -> 3.4일
배송 관련 고객문의 : 전월대비 42% 증가
고객 만족도 : 4.5 / 5.0 -> 3.7 / 5.0
물류센터 인력 : 15% 감소

주요 상품 재고 부족 : 총 12일
"""

prompt_executive= f"""
[Context]
온라인 쇼핑몰에서 최근 2개월 동안 배송과 고객 만족도 관련 문제가 발생했다.
다음은 현재 확인된 데이터다.
{business_data}

======================
[objective]
경영진이 현재 상황의 심각성을 이해하고 어떤 문제를 우선적으로 관리해야 하는지 판다낳ㄹ 수 있도록 핵심 내용을 전달한다.

======================
[Style]
경영 보고서 스타일로 작성한다.
- 핵심 수치 중심
- 불필요한 설명 최소화
- 의사결정에 필요한 내용 중심
- 문제와 대응 우선순위를 명확하게 표현

======================
[Tone]
전문적이고 객관적인 어조를 사용한다.
과장하거나 감정적으로 표현하지 않는다.

======================
[Audience]
대상은 회사의 경영진이다.
세부 운영 방법보다는
- 어떤 문제가 발생했는가
- 얼마나 심각한가
- 무엇을 우선적으로 관리해야 하는가
를 중요하게 본다.

======================
[Response]
다음 형식으로 작성한다.

[핵심 현황]
-
-
-

[주요 위험]
1.
2.

[우선 대응 영역]
1순위:
이유:
2순위:
이유:

[경영진 요약]
3문장 이내로 작성한다.
"""
executive_result = ask_gemini(prompt=prompt_executive)
print(executive_result)