# SmartHRD AI Agent (MVP)

> **직업훈련시장 정형 데이터 분석(PostgreSQL)과 관련 규정/심사기준 검색(ChromaDB RAG)을 결합한 AI 기반 의사결정 지원 에이전트**

SmartHRD AI Agent는 직업훈련기관 원장, 과정 기획자, 운영 실무자가 자연어 질문을 통해 **훈련시장 공급 현황(과정 수, 회차 수, 훈련비, 정원 등)**을 정확한 수치로 분석하고, **관련 법령·고시·심사평가 가이드·FAQ**에서 근거를 검색하여 과정 개설 및 운영 의사결정을 신속하게 내릴 수 있도록 돕는 시스템입니다.

---

## 1. 핵심 사용자 시나리오

1. **Type A (정형 시장 분석):**  
   > *"용인시 데이터분석 관련 훈련시장 현황을 분석해줘."*  
   $\rightarrow$ PostgreSQL 쿼리 기반 정확한 시장 통계(고유 과정 수, 개설 회차 수, 평균 훈련비, 기관 수) 및 LLM 해석
2. **Type B (규정 및 가이드 검색):**  
   > *"훈련과정 변경 시 어떤 규정을 확인해야 해?"*  
   $\rightarrow$ ChromaDB 시맨틱 검색을 통한 관련 법령·지침 근거 확보 및 출처(문서명, 조항, 페이지) 명시 답변
3. **Type C (복합 의사결정 지원 - Primary E2E):**  
   > *"용인에서 데이터분석 과정을 개설하려고 하는데 시장현황과 심사 시 주의사항을 알려줘."*  
   $\rightarrow$ 시장 데이터 집계와 심사 규정 검색을 동시에 수행한 후 실무형 종합 보고서로 합성

---

## 2. 시스템 아키텍처

```text
                      [사용자 자연어 질문]
                                │
                                ▼
                       [LangGraph Router]
                  (market / regulation / mixed)
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
[Market Analysis Node]                           [RAG Search Node]
 - 사전 정의된 분석 Tool                           - 공통 Document Schema
 - PostgreSQL (61.9만 Fact)                      - ChromaDB Vector Store
 - NCS 2022 Master (1,083개 세분류)              - 법령/고시/가이드/FAQ 출처 인용
        │                                               │
        └───────────────────────┬───────────────────────┘
                                ▼
                     [Result Synthesis Node]
                   (정량 수치 + 규정 근거 통합)
                                │
                                ▼
                       [Streamlit Web UI]
```

### 기술 스택별 역할 분담 원칙
* **PostgreSQL:** 정형 시장 데이터의 유일한 **Source of Truth** (LLM이 임의 수치를 생성하지 않음)
* **ChromaDB:** 비정형 문서의 의미 기반 벡터 검색 및 RAG 컨텍스트 제공
* **LangChain:** 개별 기능 부품 구현 (SQL Analysis Tool, ChromaDB Retriever, Prompt Template)
* **LangGraph:** 질문 의도 분기, 상태(State) 관리, 결과 통합을 담당하는 **워크플로우 제어 계층**
* **Streamlit:** 실무자용 웹 대시보드 및 질의응답 UI

---

## 3. 프로젝트 디렉토리 구조

```text
15_MIniProject/
├── README.md                      # 프로젝트 메인 안내서
│
├── data/
│   ├── structured/                # 정형 원천 데이터
│   │   ├── 2101-2604_국민내일배움카드_훈련과정_목록_정제본.csv (321.87 MB)
│   │   ├── NCS정보망DB(대분류별,2022년3월).xlsx (190.81 MB)
│   │   ├── ncs_codes_master.csv   # [추출완료] 1,083개 NCS 8자리 세분류 마스터
│   │   └── 산업별직종별_구인분류표.xlsx (V2 자산)
│   └── unstructured/              # 비정형 원천 문서 (총 15개)
│       ├── 법령/시행령/규칙/고시 PDF (8종)
│       ├── 첫_진입_훈련기관_운영가이드.pdf (165p)
│       ├── 2024년도 직업능력심사평가원 연차보고서.pdf (90p)
│       ├── 직업능력심사평가원_FAQ.json (58건)
│       └── 법령 위반사항_20251125.csv (52건)
│
├── docs/                          # 프로젝트 계획 및 설계 문서
│   ├── SmartHRD_AI_Agent_PRD_v1.3.md  # 제품 요구사항 정의서 (PRD)
│   ├── DATA_DICTIONARY.md             # 훈련과정 23개 컬럼 표준 데이터 사전
│   ├── DATA_AUDIT.md                  # [Phase 0] 원천 데이터 전수 감사 보고서
│   ├── DATABASE_DESIGN.md             # [Phase 0] PostgreSQL 스키마 및 인덱스 설계서
│   ├── IMPLEMENTATION_PLAN.md         # [Phase 0] 단계별 상세 구현 계획서
│   ├── PHASE1_VALIDATION_SPEC_v1.1.md # [Phase 1] 데이터 품질 및 SQL 테스트 명세서
│   ├── NCS_MATCHING_REPORT.md         # [검증보고] NCS 9대 지표 실측 검증 보고서
│   └── PROJECT_PROGRESS.md            # [진행현황] 마일스톤 및 작업 로그
│
├── pipeline/                      # 데이터 추출 및 ETL 파이프라인
│   ├── extract_ncs_master.py      # [완료] NCS 엑셀 -> 8자리 마스터 CSV 추출 스크립트
│   ├── validate_ncs_matching.py   # [완료] NCS 9대 매칭 지표 검증 파이프라인
│   └── load_training_courses.py   # [예정] 훈련과정 CSV -> DB 적재 파이프라인
│
├── database/                      # DB 연결 및 쿼리 레이어 (예정)
│   ├── connection.py
│   ├── schema.sql
│   └── queries.py
│
├── rag/                           # RAG 및 벡터 검색 레이어 (예정)
├── tools/                         # LangChain 분석 도구 (예정)
├── agent/                         # LangGraph 워크플로우 (예정)
├── app/                           # Streamlit 웹 애플리케이션 (예정)
└── evals/                         # 40문항 벤치마크 평가셋 (예정)
```

---

## 4. 현재 진행 현황 및 로드맵

| 단계 | 목표 | 상태 |
| :--- | :--- | :---: |
| **Phase 0: 저장소 & 데이터 감사** | 정형/비정형 전수 프로파일링, 설계 문서 작성, NCS 마스터 추출 | **완료** |
| **Phase 1: 정형 데이터 파운데이션** | PostgreSQL 스키마 생성, 61.9만 건 훈련과정 적재, 핵심 SQL 함수 | **다음 단계** |
| **Phase 2: 비정형 문서 수집 & RAG** | 공통 스키마 정규화, 15종 문서 청킹 및 ChromaDB 벡터 스토어 적재 | 대기 |
| **Phase 3: LangChain RAG + LLM** | 규정 검색 체인 및 출처 표기 시스템 구축 | 대기 |
| **Phase 4: LangChain 정형 분석** | 자연어-SQL 분석 도구 연결 및 수치 그라운딩 | 대기 |
| **Phase 5: LangGraph 워크플로우** | 라우터, 마켓/규정 노드, 종합 노드 결합 (E2E 테스트) | 대기 |
| **Phase 6: Streamlit 제품화** | 비개발자용 직관적인 웹 인터페이스 완성 | 대기 |
| **Phase 7: 평가 및 최적화** | 40문항 정량 평가 및 프롬프트 개선 | 대기 |

상세 진행 로그는 [`docs/PROJECT_PROGRESS.md`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/docs/PROJECT_PROGRESS.md)에서 확인하실 수 있습니다.

---

## 5. 주요 데이터 분석 결과 (Phase 0 확인 사항)

* **훈련과정 데이터:** 8,847건의 중복 제거 후 **619,537건** 확정. 복합 기본키 `(trpr_id, trpr_degr)` 유일성 100% 검증.
* **NCS 마스터 추출:** 24개 대분류에서 **1,083개 세분류 마스터**를 성공적으로 추출하여 [`data/structured/ncs_codes_master.csv`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/data/structured/ncs_codes_master.csv)로 저장 완료.
* **NCS 코드 매칭률:** 정제본 훈련과정(619,537건)과 마스터 간의 실측 매칭률은 **96.31% (596,177건)**로 우수함. 미매칭 3.69%(22,852건)는 Soft FK 및 `LEFT JOIN` 구조로 예외 처리.
* **취업률 성과 지표:** 약 90%가 결측치로 확인되어 임의 0% 치환을 금지하고, 반드시 표본 수(커버리지)를 병기하는 분석 규칙 적용.

---

## 6. 개발 환경 및 시작하기

### 환경 요구사항
* Python 3.12+
* PostgreSQL 15+ (또는 호환 환경)

### 패키지 설치
```bash
python -m pip install -r requirements.txt
```

### NCS 마스터 재추출 (필요 시)
```bash
python pipeline/extract_ncs_master.py
```
