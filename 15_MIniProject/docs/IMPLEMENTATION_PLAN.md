# SmartHRD AI Agent — Implementation Plan (Phase 0 Deliverable)

- **Date:** 2026-09-04
- **Status:** Phase 0 Complete / Gate 0 Review Ready
- **Author:** Antigravity (Advanced Agentic Assistant)
- **Target System:** SmartHRD AI Agent MVP

---

## 1. 프로젝트 개요 및 아키텍처 요약

SmartHRD AI Agent MVP는 직업훈련기관 관리자 및 실무자가 자연어 질문을 통해 **직업훈련시장 정형 데이터 분석(PostgreSQL)**과 **직업훈련 관련 법령/가이드/규정 검색(ChromaDB RAG)**을 결합하여 실무 의사결정을 내릴 수 있도록 돕는 시스템이다.

### 전체 아키텍처 흐름
```text
                       [User Natural Language Query]
                                     │
                                     ▼
                            [LangGraph Router]
                        (market / regulation / mixed)
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                                                       ▼
 [Market Analysis Node]                                   [RAG Search Node]
  - Predefined Query Tools                                 - Common Doc Schema
  - PostgreSQL (61.9만 Fact)                              - ChromaDB Vector Store
  - NCS 2022 Master                                       - Citation Grounding
         │                                                       │
         └───────────────────────────┬───────────────────────────┘
                                     ▼
                          [Result Synthesis Node]
                       (Numerical + Evidence Fusion)
                                     │
                                     ▼
                            [Streamlit Web UI]
```

---

## 2. 단계별 구현 세부 계획 (Phases 1 ~ 7)

### Phase 0: Repository & Data Audit (완료)
- **목표:** 원천 데이터 18종 전수 조사, 프로파일링 및 스키마/계획 수립
- **산출물:** `docs/DATA_AUDIT.md`, `docs/DATABASE_DESIGN.md`, `docs/IMPLEMENTATION_PLAN.md`
- **Gate 0 통과 조건:** 프로파일링 결과 보고 및 사용자 승인

---

### Phase 1: Structured Data Foundation
- **목표:** PostgreSQL 기반 `training_courses` 및 `ncs_codes` 마스터 적재, Pre-load DQ 규칙 검증, 핵심 시장지표 SQL 함수 및 Post-load SQL 테스트셋(T01~T10) 구축
- **주요 작업:**
  1. `database/connection.py`: DB 커넥션 풀 및 세션 관리
  2. `database/schema.sql`: DDL 및 인덱스 생성 (Soft FK 및 단독 기관 Key 반영)
  3. `pipeline/extract_ncs_master.py`: NCS 엑셀 $\rightarrow$ `ncs_codes` 마스터 1,083개 세분류 추출/적재
  4. `pipeline/validate_ncs_matching.py`: NCS 9대 매칭 지표 공식 산출 (96.31%, 596,177건)
  5. `pipeline/load_training_courses.py`:
     - 22개 업무 컬럼 집합(Set) 기준 스키마 검증 (순서 무관)
     - `index` 제외 완전 중복 제거 (619,537건 확정)
     - `ncsCd` 공식 정규화: NULL 유지, 문자열 변환, trailing `.0` 제거, 8자리 미만 유효 코드 `zfill(8)` 적용
     - `wkendSe`: '9'는 공식 명세 미확인 코드로 원본 보존
     - 타입 변환 실패 탐지: 원본 NULL과 non-null의 변환 실패(`original_not_null AND converted_is_null`) 엄격 분리
     - Python/pandas 기반 단순 유효성 검증 (ERROR: 중단, WARN/INFO: 로그 후 진행, 불필요한 Pandera 배제)
     - PostgreSQL Bulk Insert
  6. `database/queries.py`: T01~T10 표준 분석 SQL 및 함수 구현 (`course_count` 비가산성 준수, NCS `LEFT JOIN` 유지, 기관별 `trainst_cst_id` 단독 GROUP BY, 성과지표 Coverage 병기)
  7. `tests/test_phase1_validation.py`: V01~V06 사후 검증 및 Reference Reconciliation (Raw ↔ Cleaned ↔ DB 대조)
- **예상 파일:**
  - `database/connection.py`, `database/schema.sql`, `database/queries.py`
  - `pipeline/extract_ncs_master.py` (완료), `pipeline/validate_ncs_matching.py` (완료), `pipeline/load_training_courses.py`
  - `tests/test_phase1_validation.py`
- **Gate 1 통과 조건:** PostgreSQL 적재 완료, SQL Test Set(T01~T10) 실행 검증, 3개 층(Raw ↔ Cleaned ↔ DB) Reconciliation 일치 확인 후 Gate 1 최종 판정 (Phase 1 완료 전 Phase 2 선행 금지)


---

### Phase 2: Document Ingestion & Retrieval Foundation
- **목표:** 15종 비정형 문서를 공통 Document Schema로 정규화하고 ChromaDB에 청킹/임베딩하여 적재
- **주요 작업:**
  1. `rag/schema.py`: PRD 3.1 공통 `DocumentSchema` (Pydantic) 구현
  2. `rag/parsers.py`: PDF (pypdf/pdfplumber), JSON (FAQ), CSV (위반사례, CP949) 파서 구현
  3. `rag/chunking.py`: 문서 유형별 분할기 (법령: 조문 단위, 가이드: 섹션 단위, FAQ: 1문 1답 단위)
  4. `rag/embeddings.py`: Embedding 모델 연동 (Google GenAI 또는 로컬 HuggingFace)
  5. `pipeline/ingest_documents.py`: 파싱 $\rightarrow$ 스키마 매핑 $\rightarrow$ 유효성 검증 $\rightarrow$ ChromaDB `smart_hrd_knowledge` 컬렉션 적재
  6. Top-K 검색 단위 테스트: 대표 질의에서 원문 청크 및 메타데이터(문서명, 페이지, 조항) 정상 반환 확인
- **예상 신규 파일:**
  - `rag/__init__.py`, `rag/schema.py`, `rag/parsers.py`, `rag/chunking.py`, `rag/embeddings.py`
  - `pipeline/ingest_documents.py`
  - `tests/test_retrieval.py`
- **Gate 2 통과 조건:** 대표 규정 질의에 대해 ChromaDB에서 관련 법령/가이드 청크와 정확한 메타데이터가 Top-K로 검색되는 상태

---

### Phase 3: LangChain RAG + LLM
- **목표:** 검색된 규정 근거를 바탕으로 환각 없이 출처를 표기하는 RAG 체인 구축
- **주요 작업:**
  1. `prompts/rag_prompt.py`: 근거 중심 답변, 출처 표기 강제, 근거 부족 시 판단 보류 시스템 프롬프트 정의
  2. `rag/retriever.py`: ChromaDB Retriever 래핑 (유사도 임계값, 메타데이터 필터링)
  3. `rag/chain.py`: LangChain LCEL 기반 Retrieval-QA 체인 구축 및 Pydantic Structured Output 연동
- **Gate 3 통과 조건:** 규정 질문에 대해 출처(문서명, 페이지, 조항)를 포함한 답변 생성 및 근거 부족 질의에 대한 올바른 사권(거절) 처리

---

### Phase 4: LangChain Structured Analysis + LLM
- **목표:** 자연어 질문의 분석 조건을 파악하여 PostgreSQL 쿼리 도구를 호출하고 그 결과를 실무형으로 해석
- **주요 작업:**
  1. `tools/market_tool.py`: `database/queries.py`를 LangChain Tool로 래핑
  2. `prompts/analyst_prompt.py`: 사실(DB 수치)과 해석을 엄격히 구분하는 프롬프트
  3. `tools/query_router.py`: 사용자 자연어 질문을 검증된 파라미터(지역, 직종, 기간)로 정규화하는 파서
- **Gate 4 통과 조건:** LLM이 DB에 존재하지 않는 임의 수치를 만들어내지 않고, 실제 쿼리 결과와 100% 일치하는 수치 기반 리포트 생성

---

### Phase 5: LangGraph Integration
- **목표:** Market Analysis Node와 RAG Node를 오케스트레이션하여 혼합 질문(Type C) E2E 지원
- **주요 작업:**
  1. `agent/state.py`: `AgentState` 정의 (question, intent, sql_result, rag_result, final_answer, sources)
  2. `agent/router.py`: 의도 분류 라우터 (`market` / `regulation` / `mixed`)
  3. `agent/nodes.py`: Market Node, RAG Node, Synthesis Node, Validation Node 구현
  4. `agent/graph.py`: StateGraph 정의, 조건부 엣지 구성 및 컴파일
  5. E2E 검증: "용인에서 데이터분석 과정을 개설하려고 하는데 시장현황과 심사 시 주의사항을 알려줘" 쿼리 E2E 테스트
- **Gate 5 통과 조건:** Type A, B, C 질문에 대해 라우터가 정확히 분기하고 종합 노드에서 통합된 최종 보고서 도출

---

### Phase 6: Streamlit Productization
- **목표:** 실무자가 웹 브라우저에서 바로 사용할 수 있는 UI 완성
- **주요 작업:**
  1. `app/streamlit_app.py`:
     - 상단: 질의 입력 및 샘플 질문 원클릭 버튼 (Type A, B, C)
     - 중앙: 시장 분석 카드 (과정 수, 회차 수, 평균 훈련비 등 메트릭 지표 표시)
     - 하단 탭 1: AI 종합 분석 의견
     - 하단 탭 2: 관련 규정 및 심사기준 (문서명, 페이지 등 근거 아코디언 제공)
     - 사이드바: DB 연결 상태 및 사용 모델 정보
- **Gate 6 통과 조건:** 브라우저 환경에서 질의 $\rightarrow$ 시장 데이터 차트/메트릭 $\rightarrow$ 규정 근거 뷰어가 매끄럽게 작동

---

### Phase 7: Evaluation & Prompt Optimization
- **목표:** 정량적 벤치마크 평가셋(40문항)을 통한 품질 측정 및 프롬프트 튜닝
- **주요 작업:**
  1. `evals/dataset.json`: 질문 40건 구축 (정형 10, 규정 10, 혼합 10, 범위 외 5, 거짓전제 5)
  2. `evals/evaluate.py`: Routing 정확도, 수치 일치율(Numerical Grounding), 근거 인용 정확도 자동 측정
  3. 프롬프트 개선 및 실패 사례집(`evals/FAILURE_ANALYSIS.md`) 작성
- **Gate 7 통과 조건:** 주요 실패 유형 분석 및 전 지표 측정 가능 상태 확보

---

## 3. 의존성 및 패키지 정의 (`requirements.txt` 초안)

```text
# Data & DB
pandas>=3.0.0
openpyxl>=3.1.5
sqlalchemy>=2.0.0
psycopg[binary]>=3.3.0
pyarrow>=24.0.0

# Document & PDF
pypdf>=6.14.0
pdfplumber>=0.11.0

# VectorDB & LLM
chromadb>=1.0.0
google-genai>=2.18.0
langchain>=1.2.0
langchain-core>=1.2.0
langchain-community>=1.2.0
langgraph>=0.4.0

# Validation & Utilities
pydantic>=2.13.0
python-dotenv>=1.2.0

# UI
streamlit>=1.60.0
```

---

## 4. 사용자 결정 및 확인 필요 항목 (Open Decisions for Gate 0)

1. **PostgreSQL 호스트 환경:**
   - 현재 로컬에 `psql` 및 `docker`가 설치되어 있지 않습니다.
   - **선택 옵션:**
     - 옵션 A: 로컬 환경에 PostgreSQL 16/17 직접 설치
     - 옵션 B: 기존에 운영 중인 외부/사내 PostgreSQL 서버 접속 정보(.env) 제공
     - 옵션 C (개발/프로토타입 대안): SQLite 또는 DuckDB를 우선 활용하여 로직을 검증한 후 PostgreSQL로 이관
   - *권장: 외부/로컬 PostgreSQL 사용 여부 확정 필요.*
2. **LLM Provider 및 API Key:**
   - Google Gemini (`google-genai` SDK) 활용 여부 및 API Key 환경변수(`GEMINI_API_KEY`) 준비 상태 확인.
