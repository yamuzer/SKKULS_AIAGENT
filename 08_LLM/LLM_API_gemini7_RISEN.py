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

# 제미나이 공식가이드 프롬프팅 RISEN
# Role : 어떤 역할
# Instructions : 정확히 무엇을 수행해야 하는지
# Step : 어떤 순서로 수행해야 하는지
# End Goal : 최종적으로 어떤 결과를 만들지
# Narrowing : 분석 범위와 제한 사항



def ask_gemini(
    prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt
    )
    return interaction.output_text

performance_data = """
[고객 만족도]
2025년 4.4 / 5
2026년 3.6 / 5

[평균 배송 기간]
2025년 : 1.8일
2026년 : 3.2일

[반품률]
2025년 : 4.2%
2026년 : 7.8%

[고객 평균 응답시간]
2025년 : 3시간
2026년 : 11시간
"""

operation_data = """
[2026년 운영 정보]
물류센터 인력:
전년 대비 20% 감소

고객지원 인력:
2025년 : 18명
2026년 : 12명

신규 상품 비중 : 
전체 상품의 35%

신규 상품 관련 정보:
신규 상품군의 초기 불량 신고가 기존 상품군보다 높은 수준이다.
"""

prompt_risen = f"""
[Role]
너는 온라인 쇼핑몰의 고객경험 및 운영 데이터를 분석하는 senior data analyst이다.
경영진이 실제 개선 우선순위를 결정할 수 있도록 데이터를 근거로 분석한다.
==============================
[Instructions]
다음 데이터를 분석하여 2026년 고객 만족도 하락과 관련될 가능성이 있는 문제를 찾아라.
다음 항목을 반드시 분석한다.
- 고객 만족도 변화
- 배송기간 변화
- 반품률 변화
- 고객문의 응답시간 변화
- 운영 인력 변화
- 신규 상품 관련 문제
각 데이터가 고객 경험 악화와 어떤 관련성을 가질 수 있는지 분석한다.
==============================
[Data]
{performance_data}
==============================
[Additional Data]
{operation_data}
==============================
[Step] 
다음 순서로 분석한다.
step1.
2025년과 2026년의 주요 지표 변화를 계산하거나 비교한다.
step2.
악화된 지표를 찾는다.
step3.
악화된 지표와 운영 데이터를 연결하여 관련 가능성이 있는 요인을 찾는다.
step4.
각 문제의 중요도를 높음/보통/낮음 중 하나로 판단한다.
step5.
중요도가 높은 문제부터 개선 우선순위를 정한다.
step6.
각 우선순위 문제에 대해 실행 가능한 개선 방향을 제안한다.
==============================
[End Goal]
최종 목표는 
"2026년 고객 만족도 하락 문제를 개선하기 위해 경영진이 어떤 문제부터 대응해야 하는가?"
에 답하는 것이다.
최종 결과에는 가장 먼저 개선해야할 문제를 하나 선택하고, 그 이유와 개선 방향을 명확하게 제시한다.
==============================
[Narrowing]
다음 범위 안에서만 분석한다.
1. 제공된 데이터만 사용한다.
2. 외부 시장 상황이나 소비자 행동을 임의로 추측하지 않는다.
3. 특정 요인이 고객 만족도 하락의 직접적인 원인이라고 단정하지 않는다.
4. 데이터에서 확인 가능한 것은 "확인된 사실"로 표현한다.
5. 데이터로 직접 확인되지 않은 관계는 "관련 가능성이 있는 요인"으로 표현한다.
6. 개선 방안은 제공된 문제와 직접 연결되는 것만 제안한다.
7. 개선 방안은 최대 3개로 제한한다.
==============================
[Output]
다음 형식으로 작성한다.
1. 주요 지표 변화
고객 만족도:
배송기간: 
반품률:
고객 문의 응답시간:

2. 문제 후보
문제1:
근거:
중요도:

문제2:
근거:
중요도:

문제3:
근거:
중요도:

3. 개선 우선순위
1순위:
이유:

2순위:
이유:

3순위:
이유:

4. 개선 방안
개선방안1:
개선방안2:
개선방안3:

5. 최종 결론
3문장 이내로 작성한다.
"""

risen_result = ask_gemini(prompt=prompt_risen)
print(risen_result)
