# SmartHRD AI Agent --- MVP PRD

-   **Version:** v1.3
-   **Status:** Development Ready
-   **Product:** SmartHRD
-   **Document Purpose:** Codex 개발 인수인계 및 단계별 구현 기준
-   **Last Updated:** 2026-09-04

------------------------------------------------------------------------

## 1. 프로젝트 개요

### 1.1 Background

SmartHRD는 고용노동부 직업훈련 데이터를 기반으로 직업훈련기관 실무자의
시장분석 및 의사결정을 지원하는 데이터 서비스다.

기존 SmartHRD는 Power BI 기반으로 구축되어 있으며 사용자가 직접 데이터를
탐색하고 차트를 해석하는 방식이다.

이번 프로젝트에서는 이미 수집된 데이터를 활용하여 **정형 데이터 분석과
비정형 문서 검색을 결합한 AI Agent MVP**를 별도로 구축한다.

기존 Power BI 서비스를 즉시 대체하는 것이 목적은 아니다.

### 1.2 Product Goal

직업훈련기관 실무자가 자연어 질문을 통해:

1.  직업훈련시장 데이터를 조회·분석하고,
2.  관련 법령·가이드·매뉴얼에서 근거를 검색하고,
3.  두 결과를 결합하여 과정 기획·운영 의사결정에 필요한 정보를 얻을 수
    있도록 한다.

> **핵심 제품 정의:** 직업훈련시장 정형 데이터 분석과 직업훈련 관련 규정
> 검색을 결합한 AI 기반 의사결정 지원 Agent

------------------------------------------------------------------------

## 2. Target User & Problem

### 2.1 Target User

-   직업훈련기관 원장 및 관리자
-   과정 기획자
-   훈련 운영 실무자

### 2.2 Core Jobs

사용자가 해결하려는 핵심 질문은 다음과 같다.

-   어떤 훈련과정을 개설할 것인가?
-   특정 지역의 훈련시장 및 경쟁 상황은 어떠한가?
-   유사 과정은 얼마나 운영되고 있는가?
-   해당 과정의 시장 지표는 어떠한가?
-   과정 개설·운영 시 어떤 규정과 심사기준을 확인해야 하는가?

### 2.3 Product Principle

AI 기술 자체가 제품의 목적이 아니다.

**사용자가 직접 데이터를 탐색하고 여러 문서를 검색해야 하는 과정을 줄여,
데이터와 근거에 기반한 판단을 빠르게 만드는 것**을 우선한다.

------------------------------------------------------------------------

## 3. 보유 데이터 및 MVP 범위

MVP에서는 현재 이미 보유한 데이터만 사용한다. 신규 외부 데이터 수집은
MVP 필수 범위가 아니다.

### 3.1 Structured Data

MVP의 정형 데이터는 **훈련시장 공급 데이터 + NCS Master**로 한정한다.
산업·직종별 구인 데이터는 가치가 높지만 V2의 노동시장 수요 분석용
데이터로 보존한다.

#### A. Training Courses --- Core Fact

**Source** - 고용24 국민내일배움카드 훈련과정 API를 통해 기존 수집한
데이터

**Current Dataset Profile** - 원본 행 수: 628,384 - 원본 컬럼 수: 23 -
`index` 제외 완전 중복: 8,847행 - 중복 제거 후: 619,537행 - 중복 제거 후
`(trprId, trprDegr)` 조합 중복: 0건 - `trprId`, `trprDegr` NULL: 0건

**Role** - 훈련시장 공급(Supply) 분석 - 지역 × NCS × 과정 × 회차 × 기간
기준 집계 - AI Agent의 정형 시장분석 Source of Truth

**MVP Modeling Principle** - `training_courses` 단일 Fact 테이블로
시작한다. - `(trpr_id, trpr_degr)`를 복합 Primary Key로 사용한다. -
ID/Code 성격의 값은 문자열 타입을 우선한다. - 원본 필드의 공식 의미가
확인되지 않은 경우 의미를 추측하여 rename하지 않는다. -
기관/지역/훈련유형 dimension은 실제 필요성이 확인되기 전까지 분리하지
않는다.

``` sql
CREATE TABLE training_courses (
    trpr_id           VARCHAR NOT NULL,
    trpr_degr         INTEGER NOT NULL,

    title             TEXT NOT NULL,
    sub_title         TEXT NOT NULL,
    trainst_cst_id    VARCHAR NOT NULL,

    tra_start_date    DATE NOT NULL,
    tra_end_date      DATE NOT NULL,

    address           TEXT NOT NULL,
    ncs_cd            VARCHAR,

    train_target      TEXT NOT NULL,

    real_man          INTEGER NOT NULL,
    reg_course_man    INTEGER NOT NULL,
    yard_man          INTEGER NOT NULL,
    course_man        INTEGER NOT NULL,

    stdg_scor         NUMERIC,
    ei_empl_rate_3    NUMERIC,
    ei_empl_rate_6    NUMERIC,
    ei_empl_cnt_3     INTEGER,

    tel_no            VARCHAR,

    title_link        TEXT,
    sub_title_link    TEXT,

    wkend_se          VARCHAR,

    PRIMARY KEY (trpr_id, trpr_degr)
);
```

위 스키마는 현재 profiling 기준 MVP 초안이다. 공식 API 명세 확인 결과에
따라 타입과 NULL 제약은 조정할 수 있다.

#### B. NCS Master --- Training Occupation Classification

**Source** - `NCS정보망DB(대분류별,2022년3월).xlsx` - 24개 NCS 대분류
시트 - 대분류 → 중분류 → 소분류 → 세분류 → 능력단위 → 능력단위요소 →
수행준거 → 지식/기술/태도 구조

MVP에서는 훈련과정 시장분석에 필요한 **세분류까지의 계층만 Master Data로
추출**한다.

``` text
ncs_codes
├─ major_code
├─ major_name
├─ middle_code
├─ middle_name
├─ minor_code
├─ minor_name
├─ detail_code
└─ detail_name
```

관계:

``` text
training_courses.ncs_cd
          ↓
      ncs_codes
```

**주의** - NCS 원천파일은 2022년 3월 기준이다. - 훈련과정 데이터는
2026년까지 포함하므로 실제 `ncs_cd` 매칭률을 측정한 후 Master 사용
범위를 확정한다. - 2022년 이후 신설/개편 코드가 매칭되지 않을 가능성을
데이터 품질 이슈로 관리한다. - 능력단위·수행준거·지식·기술·태도는 원천에
보존하되 MVP PostgreSQL/VectorDB 필수 범위에서는 제외한다.

#### C. Job Demand Data --- V2 Asset

**Source** - `산업별직종별_구인분류표.xlsx`

**Observed Structure** - 2026년 7월 기준 - 80,665행 - 시군구 261개 -
산업 대분류 23개 - 직종 중분류 35개 - 직종 소분류 140개 - 측정값:
구인인원 - 상위 분류가 병합/공란 형태로 저장되어 있으므로 적재 시
forward-fill 형태의 구조 복원이 필요 - 구조 복원 후
`지역 + 산업 대분류 + 직종 중분류 + 직종 소분류` 조합은 고유하게 관리
가능

개념적 역할:

``` text
Training Courses = 훈련시장 공급(Supply)
Job Demand       = 노동시장 수요(Demand)
```

향후:

``` text
지역 × 산업 × 직종 × 구인수요
             ↓
        직종 ↔ NCS Mapping
             ↓
지역 × NCS × 훈련과정 공급
             ↓
       수요-공급 Gap 분석
```

으로 확장할 수 있다.

**MVP에서는 구인 데이터와 산업/직종 Mapping을 Agent 분석에 포함하지
않는다.** 현재는 V2 확장 자산으로 보존한다.

#### Initial Indexes

``` sql
CREATE INDEX idx_training_courses_start_date
ON training_courses (tra_start_date);

CREATE INDEX idx_training_courses_ncs
ON training_courses (ncs_cd);

CREATE INDEX idx_training_courses_address
ON training_courses (address);
```

추가 인덱스는 실제 Query Pattern과 실행계획을 확인한 후 추가한다.

#### ETL Rules

``` text
Raw CSV
   ↓
불필요한 index 컬럼 제거
   ↓
index 제외 완전중복 제거
   ↓
ID / Code / Date / Numeric 타입 정규화
   ↓
Schema & Data Quality Validation
   ↓
PostgreSQL Load
   ↓
Load Result / Error Log
```

특히 `ncsCd`는 숫자가 아닌 식별 코드로 관리한다. 코드 복원 규칙은 공식
명세 확인 후 확정하며 추측하여 zero-padding하지 않는다.

#### Semantic Metric Principles

``` text
course_count
= COUNT(DISTINCT trpr_id)

course_run_count
= 과정 회차 수
= COUNT(*) after uniqueness of (trpr_id, trpr_degr)
```

사용자의 `"과정 수"`와 `"개설 회차 수"`를 동일 지표로 취급하지 않는다.

취업률 등 결측률이 높은 성과지표는 단순 평균만 제시하지 않고 가능한 경우
계산 대상 건수/커버리지를 함께 고려한다.

#### Data Dictionary Requirement

Phase 1에서 `DATA_DICTIONARY.md`를 작성한다.

최소 항목: - 원본 컬럼명 - DB 컬럼명 - 공식 의미 - 데이터 타입 - NULL
허용 여부 - ID/Code 여부 - Agent 분석 활용 여부 - 관련 지표/주의사항

**Open Verification Items** - 고용24 API 공식 명세와 23개 훈련과정 컬럼
전체 대조 - 의미가 불명확한 원본 필드의 공식 정의 확인 -
`training_courses.ncs_cd`와 2022 NCS Master의 코드 매칭률 측정 - 지역
Master 필요 여부는 `address` 값의 표준화 수준을 확인한 뒤 결정

### 3.2 Unstructured Data

**Sources** - 법령 - 시행령 - 고시 - 심사평가 가이드 - 심사평가 매뉴얼 -
운영지침 - FAQ - 위반사례 및 기타 보유 문서

**Storage** - ChromaDB

**Role** - 규정·업무 문서의 의미 기반 검색 - RAG context 제공 -
문서명/페이지/조항 등 근거 제공

#### Common Document Schema

모든 비정형 데이터는 파일 형식과 관계없이 아래 공통 스키마로 정규화한 후
임베딩한다.

``` python
class DocumentSchema(BaseModel):
    id: str
    content: str
    document_type: str
    document_name: str
    source_file: str | None = None
    page: int | None = None
    section: str | None = None
    article: str | None = None
    effective_date: str | None = None
    year: int | None = None
```

**필수 필드:** `id`, `content`, `document_type`, `document_name`

나머지 필드는 원문에서 확인 가능한 경우에만 채우며 알 수 없는 값은
`null`로 처리한다.

초기 `document_type` 후보: `law`, `decree`, `rule`, `notice`, `guide`,
`faq`, `violation_case`, `announcement`

필요성이 확인되기 전까지 복잡한 ontology나 문서 간 관계 모델을 추가하지
않는다.

#### Document-specific Chunking

-   법령/시행령/시행규칙/고시: 조문 중심
-   가이드/매뉴얼: 제목·절·섹션 중심
-   FAQ: 질문 1건 단위
-   위반사례: 사례/행 1건 단위
-   구조 식별이 어려운 문서: 일반 Text Splitter fallback

Chunk 크기와 overlap은 Retrieval 평가 결과에 따라 조정한다.

#### Ingestion Principle

``` text
File
 ↓
File Parser
 ↓
Raw Content
 ↓
LLM Schema Normalizer
 ↓
Pydantic Validation
 ↓
Document-specific Chunking
 ↓
Embedding
 ↓
ChromaDB
```

-   파일 읽기/텍스트 추출은 Python parser가 담당한다.
-   LLM은 parser를 대체하지 않고 의미 정규화와 Schema Mapping만
    담당한다.
-   LLM은 시스템이 정의한 공통 Schema에 맞추며 임의의 field를 만들지
    않는다.
-   Structured Output을 우선 사용한다.
-   Validation을 통과한 데이터만 embedding한다.
-   원문에서 확인할 수 없는 metadata는 추측하지 않는다.

## 4. MVP 핵심 사용자 시나리오

### Type A --- Structured Analysis

> "용인시 데이터분석 관련 훈련시장 현황을 분석해줘."

처리: 1. 질문에서 분석 조건 파악 2. PostgreSQL 기반 시장 데이터 조회 3.
검증된 집계 결과 생성 4. LLM이 결과를 실무적으로 해석

### Type B --- Regulation / Document Search

> "훈련과정 변경 시 어떤 규정을 확인해야 해?"

처리: 1. ChromaDB에서 관련 Chunk 검색 2. 관련 법령·가이드·매뉴얼 근거
확보 3. LLM이 검색된 근거만을 중심으로 답변 4. 문서명·페이지·섹션 등
출처 표시

### Type C --- Mixed Analysis

> **"용인에서 데이터분석 과정을 개설하려고 하는데 시장현황과 심사 시
> 주의사항을 알려줘."**

처리: 1. 시장분석 필요성 판단 2. PostgreSQL 조회 3. 규정검색 필요성 판단
4. ChromaDB 검색 5. 두 결과 통합 6. 근거 기반 최종 답변

**Type C를 MVP의 Primary End-to-End Test로 사용한다.**

------------------------------------------------------------------------

## 5. Functional Requirements

### FR-01. 정형 데이터 분석

시스템은 PostgreSQL에 저장된 실제 데이터를 기반으로 조건별 조회·집계
결과를 제공해야 한다.

초기에는 자유도가 높은 unrestricted Text-to-SQL보다 **검증된 분석
함수/Query Tool을 우선**한다.

예시: - `get_market_summary()` - `get_course_count()` -
`get_institution_count()` - `get_course_trend()` -
`get_region_summary()`

실제 함수는 데이터 profiling 후 필요한 분석 단위에 맞게 확정한다.

### FR-02. 비정형 문서 검색

시스템은 사용자의 자연어 질문과 의미적으로 관련된 문서 Chunk를 검색해야
한다.

반환 결과에는 가능한 범위에서 다음을 포함한다.

-   원문 Chunk
-   document name
-   document type
-   page
-   section
-   source

### FR-02A. Common Document Ingestion

시스템은 서로 다른 형식의 비정형 데이터를 공통 Document Schema로
정규화할 수 있어야 한다.

-   Parser는 파일의 원시 구조/텍스트를 추출한다.
-   LLM Schema Normalizer는 추출 결과를 고정된 공통 Schema에 매핑한다.
-   Structured Output + Pydantic Validation을 사용한다.
-   확인할 수 없는 metadata는 `null`로 처리한다.
-   Validation 실패 데이터는 임베딩하지 않는다.

### FR-02B. Future User File Upload

향후 사용자는 Streamlit에서 직접 비정형 파일을 업로드하여 Knowledge
Base에 추가할 수 있어야 한다.

``` text
User Upload
   ↓
Parser
   ↓
LLM Schema Normalizer
   ↓
Schema Preview
   ↓
User Review / Edit
   ↓
Validation
   ↓
Chunking / Embedding
   ↓
ChromaDB
```

사용자 업로드 UI와 승인 단계는 **V2 범위**다. 다만 MVP ingestion
pipeline은 향후 UI만 연결할 수 있도록 파일 입력과 정규화/검증/임베딩
로직을 분리한다.

### FR-03. RAG 답변

LLM은 검색된 문서 근거를 사용하여 규정·업무 질문에 답해야 한다.

근거가 부족하면 추측하지 않고 부족함을 명시한다.

### FR-04. 질문 Routing

시스템은 질문을 최소 다음 세 유형으로 처리할 수 있어야 한다.

-   `market`
-   `regulation`
-   `mixed`

### FR-05. 결과 통합

혼합 질문에서는 정형 데이터 분석 결과와 비정형 문서 검색 결과를 구분한
뒤 하나의 실무형 답변으로 종합한다.

### FR-06. 근거 표시

규정 관련 답변은 가능한 경우 문서명과 페이지/섹션을 표시한다.

시장분석 결과는 실제 DB 조회 결과를 기반으로 한다.

### FR-07. Streamlit UI

사용자는 브라우저에서 자연어 질문을 입력하고 분석 결과 및 근거를 확인할
수 있어야 한다.

------------------------------------------------------------------------

## 6. System Architecture

``` text
                     [Existing Data Sources]

        Structured                          Unstructured
 훈련과정 + NCS Master              법령/시행령/가이드/매뉴얼
          │                                  │
          ▼                                  ▼
   Python Data Pipeline              Document Pipeline
          │                         Load/Clean/Normalize/
          ▼                           Chunk/Embed
     PostgreSQL                           ChromaDB
          │                                  │
          ▼                                  ▼
 LangChain Analysis Tool             LangChain RAG Tool
          │                                  │
          └──────────────┬───────────────────┘
                         ▼
                     LangGraph
            Router / State / Workflow
                         │
                         ▼
                 Result Synthesis
                         │
                         ▼
                     LLM API
                         │
                         ▼
                     Streamlit
```

### 핵심 설계 원칙

**LangChain으로 개별 기능을 먼저 완성하고, 검증된 기능을 LangGraph
Node로 연결한다.**

``` text
PostgreSQL → LangChain SQL/Analysis Tool ─┐
                                          ├→ LangGraph → LLM → Streamlit
ChromaDB   → LangChain RAG Tool ──────────┘
```

LangChain과 LangGraph를 처음부터 동시에 구현하지 않는다.

------------------------------------------------------------------------

## 7. Technology Responsibilities

### 7.1 Python Pipeline

역할: - 데이터 입력 - validation - cleaning/transform - PostgreSQL
적재 - 문서 전처리 - 적재 결과 logging

파이프라인은 재실행 가능하고 실패 원인을 확인할 수 있도록 구현한다.

### 7.2 PostgreSQL

역할: - 정형 데이터의 Source of Truth - 정확한 수치 조회 - 필터링 -
JOIN - 집계 - 통계 계산

LLM이 PostgreSQL의 역할을 대신하지 않는다.

### 7.3 ChromaDB

역할: - 비정형 문서 embedding 저장 - semantic retrieval - RAG context
검색

정확한 수치 집계 목적으로 사용하지 않는다.

### 7.4 LangChain

LangChain은 **개별 AI 기능을 구성하고 외부 자원과 LLM을 연결하는
계층**으로 사용한다.

적용 영역: - Document Loader / Text Splitter - Embedding integration -
ChromaDB Retriever - RAG Chain - Prompt Template - Output Parser -
PostgreSQL 분석 기능의 Tool abstraction - Regulation Search Tool - LLM
integration

즉, LangChain은 각 Node 내부에서 실제 기능을 수행하는 부품을 만든다.

### 7.5 LangGraph

LangGraph는 **검증된 LangChain 기반 기능들을 어떤 순서와 조건으로
실행할지 제어하는 Workflow 계층**으로 사용한다.

적용 영역: - State 관리 - Intent routing - Market/RAG/Mixed 분기 - Tool
실행 순서 - 결과 통합 - 필요 시 validation/retry

LangGraph 자체가 SQL이나 Retrieval을 수행하는 것이 아니다.

### 7.6 LLM API

역할: - 자연어 질문 이해 - routing 보조 - 검색/분석 결과 해석 - 최종
답변 생성

Provider와 model은 환경설정으로 분리한다.

API Key는 코드에 하드코딩하지 않는다.

### 7.7 Prompt Engineering

프롬프트는 코드와 분리해 관리한다.

원칙: 1. DB에 없는 수치를 생성하지 않는다. 2. 검색되지 않은 규정을
사실처럼 답하지 않는다. 3. SQL 결과와 RAG 근거를 구분한다. 4. 근거가
부족하면 판단 보류를 허용한다. 5. 사실과 AI 해석을 구분한다. 6. 간결한
실무형 답변을 우선한다. 7. 향후 versioning/evaluation이 가능하도록
관리한다.

### 7.8 Streamlit

역할: - 자연어 질문 입력 - 주요 시장 결과 표시 - AI 해석 표시 -
규정/문서 근거 표시

MVP에서는 별도 React frontend 또는 FastAPI backend 분리를 요구하지
않는다.

------------------------------------------------------------------------

## 8. LangGraph Workflow

### 8.1 Conceptual State

초기 State는 최소한으로 유지한다.

``` python
class AgentState(TypedDict):
    question: str
    intent: str | None
    sql_result: dict | None
    rag_result: list | None
    answer: str | None
```

실제 구현 시 필요한 필드만 추가한다.

### 8.2 Workflow

``` text
START
  │
  ▼
Router
  │
  ├── market ─────→ Market Analysis Node ────┐
  │                                           │
  ├── regulation ─→ RAG Node ────────────────┤
  │                                           │
  └── mixed ──────→ Market + RAG Nodes ──────┤
                                              ▼
                                         Synthesis
                                              │
                                              ▼
                                          Validation
                                              │
                                              ▼
                                             END
```

초기 버전에서 Multi-Agent 구조를 만들지 않는다.

------------------------------------------------------------------------

## 9. Data Processing Design

### 9.1 Structured Pipeline

``` text
Existing Raw CSV
      ↓
Drop Source Index
      ↓
Exact Duplicate Removal
      ↓
Type Normalization
      ↓
Schema / Data Quality Validation
      ↓
PostgreSQL Load
      ↓
SQL Verification
      ↓
ETL Log
```

원본 데이터 profiling 결과를 기준으로 MVP에서는 `training_courses` 단일
테이블을 사용한다.

핵심 규칙: - `(trpr_id, trpr_degr)` 복합키 유일성 검증 - ID/Code는
문자열 우선 - 날짜는 PostgreSQL `DATE`로 변환 - 결측값을 임의의 0으로
치환하지 않음 - `ncs_cd` 복원 규칙은 공식 명세 확인 후 적용 - 원본 필드
의미가 확정되기 전에는 비즈니스 의미를 추측하여 rename하지 않음 - Load
후 주요 지표를 SQL로 재검증

`DATA_DICTIONARY.md`를 정형 데이터의 의미와 Agent 분석 지표를 연결하는
최소 Semantic Layer 문서로 사용한다.

### 9.2 Document Pipeline

``` text
PDF / TXT / JSON / other supported docs
      ↓
Text Extraction
      ↓
Cleaning
      ↓
Chunking
      ↓
Metadata
      ↓
Embedding
      ↓
ChromaDB
      ↓
Retrieval Test
```

Chunk 크기와 overlap은 사전에 고정된 정답으로 두지 않고 실제 문서 구조와
Retrieval 평가를 통해 조정한다.

------------------------------------------------------------------------

# 10. 단계별 개발 Roadmap

## Phase 0 --- Repository & Data Audit

### Goal

개발 전에 현재 코드와 데이터 상태를 정확히 파악한다.

### Tasks

-   repository 구조 분석
-   기존 Python 코드 확인
-   정형 데이터 위치/형식/컬럼 profiling
-   비정형 문서 유형 및 파일 형식 확인
-   기존 ETL/전처리/RAG 코드 확인
-   환경변수/dependency 확인
-   재사용 가능한 코드 식별
-   PostgreSQL 데이터 모델 초안
-   구현 영향 파일 목록 작성

### Deliverables

-   `DATA_AUDIT.md`
-   `DATABASE_DESIGN.md`
-   `IMPLEMENTATION_PLAN.md`

### Gate 0

**사용자에게 분석 결과와 설계 초안을 보고하고 승인받기 전 Phase 1을
구현하지 않는다.**

------------------------------------------------------------------------

## Phase 1 --- Structured Data Foundation

### Goal

LLM 없이도 정확한 훈련시장 분석이 가능한 최소 PostgreSQL 기반과 NCS 분류
Master, 핵심 지표 정의를 구축한다.

### MVP Scope

``` text
training_courses  ← Fact
       │
       │ ncs_cd
       ▼
   ncs_codes      ← Master
```

구인시장 데이터와 산업/직종 Mapping은 Phase 1 범위에 포함하지 않는다.

### Tasks

1.  고용24 API 공식 명세와 현재 훈련과정 23개 컬럼 대조
2.  `DATA_DICTIONARY.md` 작성
3.  `training_courses` 단일 Fact schema 최종 확정
4.  `(trpr_id, trpr_degr)` PK 및 최소 인덱스 적용
5.  `index` 제거 및 완전중복 제거
6.  ID/Code/Date/Numeric 타입 정규화
7.  재실행 가능한 CSV → PostgreSQL load pipeline 작성
8.  NCS 원천파일에서 대/중/소/세분류 Master 추출
9.  `training_courses.ncs_cd ↔ ncs_codes` 매칭률 검증
10. data quality validation 및 ETL logging
11. 최소 분석 함수/SQL 작성
12. 핵심 Semantic Metric 정의 및 검증

### Minimum Metrics

-   고유 과정 수 (`course_count`)
-   개설 회차 수 (`course_run_count`)
-   지역별 과정/회차 현황
-   NCS 대/중/소/세분류별 과정/회차 현황
-   기간별 개설 추이

비용, 정원, 등록인원, 취업성과 등은 공식 API 필드 의미 확인 후 지표에
포함한다.

### Deliverables

-   `DATA_DICTIONARY.md`
-   PostgreSQL schema
-   `training_courses` load pipeline
-   `ncs_codes` extraction/load logic
-   NCS 코드 매칭률 결과
-   최소 SQL/analysis functions
-   ETL/data quality test result

### Gate 1

다음을 모두 만족해야 Phase 2로 진행한다.

-   공식 API 명세와 주요 원본 컬럼 의미가 대조되어 있다.
-   중복 제거 및 타입 변환 규칙이 재현 가능하다.
-   `(trpr_id, trpr_degr)` 유일성이 검증된다.
-   `training_courses`가 PostgreSQL에 정상 적재된다.
-   NCS 4단계 Master가 생성된다.
-   훈련과정 NCS 코드와 Master의 매칭률 및 미매칭 원인이 확인된다.
-   LLM 없이 핵심 시장지표를 SQL로 계산할 수 있다.
-   `course_count`와 `course_run_count` 등 핵심 지표가 문서화되어 있다.
-   계산 결과가 원본 데이터와 대조 검증되어 있다.

## Phase 2 --- Document Ingestion & Retrieval Foundation

### Goal

현재 보유 문서뿐 아니라 향후 추가되는 비정형 파일도 공통 Document
Schema로 정규화하여 검색 가능한 Knowledge Base로 적재할 수 있는 최소
ingestion pipeline을 구축한다.

### MVP Scope

MVP에서는 **개발자가 지정한 파일을 처리하는 pipeline까지만** 구현한다.

``` text
PDF / CSV / JSON / TXT
        ↓
File Parser
        ↓
Raw Content
        ↓
LLM Schema Normalizer
        ↓
Pydantic Validation
        ↓
Document-specific Chunking
        ↓
Embedding
        ↓
ChromaDB
        ↓
Retrieval Test
```

### Tasks

1.  document inventory
2.  파일 유형별 parser 구현 또는 기존 코드 재사용
3.  Common Document Schema 구현
4.  LLM Structured Output 기반 Schema Normalizer 구현
5.  Pydantic validation
6.  문서 유형별 chunking
7.  embedding
8.  단일 ChromaDB collection 적재
9.  Top-K retrieval 테스트
10. 처리/validation 실패 기록

### Collection

초기 collection은 하나를 우선한다.

``` text
smart_hrd_knowledge
```

문서 유형은 `document_type` metadata로 구분한다.

### Gate 2

서로 다른 파일 형식의 보유 문서를 공통 Schema로 변환하고 Validation 후
ChromaDB에 적재하여, 대표 질의에서 관련 Chunk와 정확한 source metadata를
검색할 수 있어야 한다.

**사용자 파일 업로드 UI는 Gate 2 완료 조건에 포함하지 않는다.**

## Phase 3 --- LangChain RAG + LLM

### Goal

비정형 문서 검색을 근거 기반 질의응답 기능으로 완성한다.

### Flow

``` text
Question
   ↓
LangChain Retriever
   ↓
Relevant Chunks
   ↓
Prompt
   ↓
LLM
   ↓
Output Parser
   ↓
Answer + Sources
```

### Tasks

-   retriever 연결
-   RAG prompt 작성
-   LLM 연결
-   output format 정의
-   source 표시
-   근거 부족 처리

### Gate 3

**검색된 문서를 근거로 답변하고 출처를 함께 제공할 수 있어야 한다.**

------------------------------------------------------------------------

## Phase 4 --- LangChain Structured Analysis + LLM

### Goal

자연어 질문을 검증된 정형 데이터 분석 기능과 연결한다.

### Flow

``` text
Question
   ↓
Condition / Intent Interpretation
   ↓
LangChain Analysis Tool
   ↓
PostgreSQL
   ↓
Verified Result
   ↓
LLM Interpretation
```

### Tasks

-   분석 함수/Query Tool 정의
-   Tool abstraction
-   자연어 조건 해석
-   DB 결과 전달
-   LLM 해석
-   numerical grounding 검증

### Principle

초기에는 unrestricted Text-to-SQL을 기본값으로 사용하지 않는다. 실제
필요성이 확인되면 범위를 제한해 확장한다.

### Gate 4

**자연어 질문에 대한 최종 답변의 수치가 PostgreSQL 원본 결과와 일치해야
한다.**

------------------------------------------------------------------------

## Phase 5 --- LangGraph Integration

### Goal

독립적으로 검증된 Structured Analysis와 RAG를 하나의 Workflow로
통합한다.

### Tasks

-   AgentState 정의
-   Router node
-   Market node
-   RAG node
-   Mixed path
-   Synthesis node
-   Validation node
-   CLI/test 환경 E2E 검증

### Primary Test

> "용인에서 데이터분석 과정을 개설하려고 하는데 시장현황과 심사 시
> 주의사항을 알려줘."

### Gate 5

**하나의 질문에서 필요한 경우 PostgreSQL과 ChromaDB를 모두 사용하고 근거
기반 통합 답변을 생성해야 한다.**

이 단계에서 **AI Agent Core MVP**가 완성된다.

------------------------------------------------------------------------

## Phase 6 --- Streamlit Productization

### Goal

비개발자가 브라우저에서 Agent를 사용할 수 있도록 한다.

### MVP UI

``` text
┌────────────────────────────────────┐
│ SmartHRD AI Agent                  │
│                                    │
│ 무엇을 분석할까요?                 │
│ [_______________________________]  │
│                         [분석하기] │
├────────────────────────────────────┤
│ 시장 분석                          │
│                                    │
│ AI 분석                            │
│                                    │
│ 관련 규정 / 심사기준               │
│                                    │
│ 근거 / Sources                     │
└────────────────────────────────────┘
```

### Principle

기존 Power BI 전체를 Streamlit으로 재개발하지 않는다.

### Gate 6

**브라우저에서 질문 → 분석 → 규정 근거 확인까지 End-to-End로 사용할 수
있어야 한다.**

------------------------------------------------------------------------

## Phase 7 --- Evaluation & Prompt Optimization

### Goal

"잘 되는 것 같다"가 아니라 품질을 측정하고 개선할 수 있는 상태를 만든다.

### Evaluation Dataset

초기 목표 예시:

-   Structured questions: 10
-   RAG questions: 10
-   Mixed questions: 10
-   Out-of-scope questions: 5
-   Ambiguous / false-premise questions: 5

총 40개 내외에서 시작하되 실제 개발 상황에 맞게 조정한다.

### Metrics

-   Routing Accuracy
-   Retrieval Relevance
-   Data/Numerical Accuracy
-   Groundedness
-   Source Accuracy
-   Response Usefulness

### Prompt Workflow

``` text
Prompt v0.1
    ↓
Evaluation
    ↓
Failure Analysis
    ↓
Prompt v0.2
    ↓
Evaluation
```

### Gate 7

**대표 평가셋으로 핵심 품질을 반복 측정할 수 있고 주요 실패 유형이
문서화되어야 한다.**

------------------------------------------------------------------------

## 11. MVP Acceptance Criteria

다음을 모두 만족하면 MVP 완료로 판단한다.

-   [ ] 실제 정형 데이터 schema가 분석되어 있다.
-   [ ] 정형 데이터가 PostgreSQL에 정상 적재된다.
-   [ ] 주요 시장지표를 SQL/분석 함수로 정확히 계산할 수 있다.
-   [ ] 비정형 문서가 전처리·Chunking·Embedding되어 ChromaDB에 저장된다.
-   [ ] 대표 질의에서 관련 Chunk와 metadata가 검색된다.
-   [ ] LangChain RAG가 근거 기반 답변과 출처를 반환한다.
-   [ ] LangChain Structured Analysis가 DB 결과와 일치하는 답변을
    만든다.
-   [ ] LangGraph가 market/regulation/mixed 질문을 적절히 처리한다.
-   [ ] 혼합 질문에서 필요한 두 데이터 경로를 모두 사용할 수 있다.
-   [ ] LLM이 DB에 없는 수치를 사실처럼 생성하지 않는다.
-   [ ] 규정 답변에 확인 가능한 근거가 표시된다.
-   [ ] Streamlit에서 End-to-End 사용이 가능하다.
-   [ ] 평가 Dataset과 최소 평가 절차가 존재한다.

------------------------------------------------------------------------

## 12. Error & Safety Principles

### Data Grounding

-   DB에 없는 수치를 생성하지 않는다.
-   검색 문서에 없는 규정을 만들어내지 않는다.
-   데이터가 없으면 `데이터 없음` 또는 `판단 근거 부족`으로 처리한다.

### Query Safety

-   PostgreSQL Agent/Tool에는 원칙적으로 read-only 권한을 사용한다.
-   생성형 SQL을 도입할 경우 SELECT 중심으로 제한하고 destructive
    query를 허용하지 않는다.
-   사용자 입력을 문자열 연결 방식으로 SQL에 직접 삽입하지 않는다.

### Source Transparency

-   시장분석과 규정검색의 근거를 구분한다.
-   문서 metadata가 없는 경우 존재하는 것처럼 만들지 않는다.

------------------------------------------------------------------------

## 13. Suggested Project Structure

``` text
smartHRD-ai/
│
├── data/
│   ├── structured/
│   └── documents/
│
├── pipeline/
│   ├── load_training_data.py
│   ├── preprocess_documents.py
│   └── build_vectorstore.py
│
├── database/
│   ├── connection.py
│   ├── schema.sql
│   └── queries.py
│
├── rag/
│   ├── embeddings.py
│   ├── retriever.py
│   └── chain.py
│
├── tools/
│   ├── market_tool.py
│   └── regulation_tool.py
│
├── agent/
│   ├── state.py
│   ├── nodes.py
│   └── graph.py
│
├── prompts/
│   ├── router.py
│   ├── rag.py
│   └── analyst.py
│
├── app/
│   └── streamlit_app.py
│
├── evals/
│   ├── dataset.*
│   └── README.md
│
├── tests/
│
├── .env.example
├── requirements.txt
├── README.md
└── PRD.md
```

기존 repository 구조가 존재할 경우 이 구조를 강제로 적용하지 않는다.
먼저 기존 구조를 분석하고 최소 변경을 우선한다.

------------------------------------------------------------------------

## 14. Out of Scope --- MVP

현재 MVP에서는 다음을 구현하지 않는다.

-   Knowledge Graph
-   Neo4j
-   Multi-Agent architecture
-   사용자 로그인/권한 시스템
-   기관별 personalization
-   실시간 알림
-   경쟁기관 Monitoring Agent
-   신규 채용공고 수집
-   사람인/잡코리아 연동
-   예측 모델
-   자동 과정 생성
-   React frontend
-   FastAPI backend 분리
-   기존 Power BI 전체 대체
-   필요성이 검증되지 않은 microservice/async 분산구조

------------------------------------------------------------------------

## 15. V2 Candidates

MVP 완료 및 사용자 검증 후 우선순위를 다시 결정한다.

### 15.1 노동시장 수요 데이터 결합

보유한 `산업별직종별_구인분류표.xlsx` 구조를 기반으로 지역 × 산업 × 직종
× 월 구인인원 데이터를 추가한다.

목표:

``` text
구인시장 수요
지역 × 산업 × 직종
        ↓
직종 ↔ NCS Mapping
        ↓
훈련시장 공급
지역 × NCS × 과정
        ↓
수요-공급 Gap 분석
```

현재 보유 파일은 2026년 7월 단월 데이터이므로 MVP 시계열 분석에는
사용하지 않는다. 향후 월별 데이터를 누적할 수 있을 때 V2 Fact 구조와
Mapping 전략을 별도로 설계한다.

### 15.2 Semantic Market Search

훈련과정명, 직종/NCS 설명 등을 embedding하여 `"AI Agent 관련 과정"`,
`"반도체 관련 과정"` 같은 자연어 시장 세그먼트 분석을 지원한다.

### 15.3 NCS 상세역량 활용

NCS 원천파일의 능력단위·능력단위요소·수행준거·지식·기술·태도 텍스트는
원천에 보존한다.

MVP에서는 사용하지 않지만 향후 다음 기능의 VectorDB 후보로 검토한다.

-   자연어 직무/NCS 검색
-   훈련과정과 요구역량 매칭
-   직무별 지식·기술·태도 탐색

실제 사용자 요구가 확인되기 전에는 임베딩하지 않는다.

### 15.4 User-managed Knowledge Base

사용자가 Streamlit에서 새로운 법령·가이드·매뉴얼·FAQ 등의 파일을 직접
업로드하고 Knowledge Base에 추가할 수 있도록 한다.

``` text
파일 선택
   ↓
자동 Parser / Schema Mapping
   ↓
정규화 결과 Preview
   ↓
사용자 확인 또는 수정
   ↓
Validation
   ↓
Embedding
   ↓
Knowledge Base 반영
```

원칙: - LLM이 생성한 주요 metadata를 사용자가 확인할 수 있게 한다. -
임베딩 전에 문서 유형과 metadata를 검토·수정할 수 있게 한다. - 중복
처리, 삭제, 재임베딩, 버전관리는 실제 운영 필요성을 확인한 뒤 확장한다.

### 15.5 Knowledge Graph

다음과 같은 다단계 관계 탐색의 실제 필요성이 확인될 경우 검토한다.

``` text
산업 ↔ 직종 ↔ NCS ↔ 훈련과정 ↔ 규정/가이드
```

Knowledge Graph는 학습 목적만으로 도입하지 않는다.

### 15.6 Monitoring Agent

경쟁기관/과정/시장 변화를 자동 탐지하고 의미 있는 변화만 사용자에게
제공한다.

------------------------------------------------------------------------

## 16. Development Principles

### Simple is Best

현재 요구사항을 해결하는 가장 단순한 구현을 우선한다.

### Evidence First

AI의 표현보다 데이터와 문서 근거를 우선한다.

### Separation of Responsibilities

-   PostgreSQL = 정확한 정형 데이터
-   ChromaDB = 의미 기반 문서 검색
-   LangChain = 개별 LLM/Retrieval/Tool 기능 구성
-   LangGraph = 기능 간 Workflow orchestration
-   LLM = 질문 이해와 결과 해석
-   Streamlit = UI

### Independent Verification First

RAG와 Structured Analysis를 각각 독립적으로 검증한 뒤 LangGraph로
통합한다.

### Build Before Optimize

초기 단계에서 필요성이 없는 abstraction이나 인프라를 만들지 않는다.

### Preserve Existing Work

기존 SmartHRD 코드와 데이터 Pipeline을 먼저 파악하고 작동하는 기능을
이유 없이 재작성하지 않는다.

------------------------------------------------------------------------

## 17. Codex Development Protocol

Codex는 한 번에 전체 MVP를 구현하지 않는다.

각 Phase마다 다음 절차를 따른다.

``` text
Phase 분석
   ↓
변경 계획 제시
   ↓
사용자 승인
   ↓
해당 Phase만 구현
   ↓
테스트
   ↓
결과/변경사항 보고
   ↓
사용자 승인
   ↓
다음 Phase
```

### 필수 규칙

1.  다음 Phase를 선행 구현하지 않는다.
2.  대규모 refactoring 전에 사용자 승인을 받는다.
3.  기존 코드 재사용 가능성을 먼저 확인한다.
4.  실제 데이터 schema를 확인하지 않고 DB schema를 추측하지 않는다.
5.  실제 문서를 확인하지 않고 metadata를 추측하지 않는다.
6.  필요성이 없는 라이브러리/서비스를 추가하지 않는다.
7.  각 Phase 완료 시 테스트 결과와 남은 리스크를 보고한다.
8.  환경변수와 secret을 repository에 커밋하지 않는다.

------------------------------------------------------------------------

## 18. First Instruction to Codex

이 PRD를 읽은 후 **전체 기능을 구현하지 말 것.**

현재 수행할 작업은 **Phase 0 --- Repository & Data Audit**뿐이다.

### 수행할 작업

1.  Repository 전체 구조를 분석한다.
2.  현재 보유한 정형/비정형 데이터 위치와 형식을 확인한다.
3.  기존 Pipeline, 데이터 전처리, embedding/RAG 관련 코드를 찾는다.
4.  정형 데이터의 실제 컬럼, 타입, 중복, null, PK 후보를 profiling한다.
5.  비정형 문서의 파일 유형과 metadata 확보 가능 범위를 조사한다.
6.  재사용 가능한 코드와 수정이 필요한 코드를 구분한다.
7.  PostgreSQL 데이터 모델 초안을 작성한다.
8.  이후 Phase별 예상 변경 파일과 구현 순서를 제안한다.
9.  발견한 불확실성, 데이터 품질 문제, 기술적 리스크를 별도로 기록한다.

### 산출물

-   `DATA_AUDIT.md`
-   `DATABASE_DESIGN.md`
-   `IMPLEMENTATION_PLAN.md`

### 금지

이 단계에서는: - PostgreSQL 전체 구축 - ChromaDB 구축 - LangChain Agent
구현 - LangGraph 구현 - Streamlit 구현 - 대규모 refactoring

을 수행하지 않는다.

Phase 0 결과를 사용자에게 보고하고 승인받은 후 Phase 1을 시작한다.
