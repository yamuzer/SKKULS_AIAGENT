# SmartHRD AI Agent — Phase 2 Document Inventory

- **Version:** v1.1
- **Status:** Phase 2 pre-work / sample-reviewed
- **Source of Truth:** `SmartHRD_AI_Agent_PRD_v1.3.md`
- **Basis:** 실제 보유 파일 샘플 + `DATA_AUDIT.md` + `IMPLEMENTATION_PLAN.md`
- **Scope:** 비정형 문서 Inventory 및 Parser / Chunking / Metadata 기준
- **Important:** Phase 1 Gate PASS 전에는 Phase 2 구현을 시작하지 않는다.

---

## 1. 검토 결과 요약

실제 파일을 열어 다음 5개 대표 유형을 확인했다.

```text
FAQ JSON
위반사례 CSV
법령 PDF
운영가이드 PDF
K-Digital 심사평가 공고 PDF
```

판정:

```text
Phase 2 Inventory: PASS
Phase 2 Implementation: 아직 시작하지 않음
```

초안 대비 핵심 수정:

1. FAQ는 `question + answers[]` 구조이므로 질문 단위 chunk 안에 복수 answer를 보존한다.
2. 위반사례 CSV는 현재 확인 기준 `위반항목` 단일 컬럼이므로 존재하지 않는 metadata를 만들지 않는다.
3. 법령 PDF는 `제N조` 패턴과 시행일이 텍스트로 안정적으로 추출되어 조문 parser 적용 가능성이 높다.
4. 운영가이드는 목차/부/장/소제목이 텍스트로 확인되어 section 기반 chunking이 적합하다.
5. K-Digital 공고는 표가 텍스트로 평탄화되지만 심사항목 구조는 상당 부분 유지된다. `pdfplumber`는 실제 손실이 발생하는 표에만 fallback으로 사용한다.

---

## 2. 공통 Document Schema

```text
Document
- id
- content
- metadata
  - document_type
  - document_name
  - source_file
  - page
  - section
  - article
  - effective_date
  - year
```

필수:

```text
id
content
document_type
document_name
```

원칙:

- 원문에서 확인할 수 없는 metadata는 `null`
- parser/LLM이 metadata를 추측하지 않는다.
- `source_file`은 원본 파일명을 유지한다.
- `page`는 PDF 원본 페이지를 추적할 수 있을 때 저장한다.
- `section`, `article`은 실제 텍스트 구조에서 확인될 때만 저장한다.
- 파일명에서 명확히 드러나는 연도/시행일을 metadata로 사용할 수 있으나, 문서 본문과 충돌하면 본문 확인을 우선한다.

---

## 3. 검토 완료 Document Inventory

| # | 파일 | document_type | Parser | Primary Chunk | 확인된 Metadata / 구조 | 판정 |
|---:|---|---|---|---|---|---|
| 1 | `직업능력심사평가원_FAQ.json` | `faq` | `json` | 질문 1건 | `question`, `category`, `answer_count`, `answers[].answer`, `answers[].page`, `answers[].source_file` | PASS |
| 2 | `학교법인한국기술교육대학교_직업능력심사평가원 법령 위반사항_20251125.csv` | `violation_case` | `pandas` | 행 1건 | 현재 확인 기준 `위반항목` 단일 컬럼 | PASS |
| 3 | 고용보험법 / 평생직업능력법 등 법률 | `law` | `pypdf` | 조문 | `제N조`, 장, 시행일, 개정 정보, page | PASS |
| 4 | 시행령 | `enforcement_decree` | `pypdf` | 조문 | 법령형 구조 | 공통 parser 재사용 |
| 5 | 시행규칙 | `enforcement_rule` | `pypdf` | 조문 | 법령형 구조 | 공통 parser 재사용 |
| 6 | 고용노동부 고시/운영규정 | `notice` | `pypdf` | 조문 | 조문/장/절 구조 | 공통 parser 우선 |
| 7 | `첫_진입_훈련기관_운영가이드.pdf` | `guide` | `pypdf` | 부/장/소제목 | CONTENTS, 1부/2부, 번호형 장·소제목, page | PASS |
| 8 | `2024년도 직업능력심사평가원 연차보고서.pdf` | `report` | `pypdf` | 섹션/소제목 | section/page | 기존 Audit 기준, 구현 전 샘플 재확인 |
| 9 | `붙임. 2026년도 K-디지털 트레이닝 AI 캠퍼스 심사평가 계획 공고.pdf` | `evaluation_notice` | `pypdf` 우선 | 제목/심사항목/섹션 | 신청방법, 심사절차, 1·2차 심사, 심사항목, page | PASS with table caution |
| 10 | `고용24_국민내일배움카드_훈련과정API_목록.pdf` | `api_spec` | 별도 | - | 정형 Data Dictionary 근거 | MVP RAG 제외 권장 |

---

## 4. FAQ JSON — 확정 규칙

실제 구조:

```text
[
  {
    question
    category
    answer_count
    answers: [
      {
        answer
        page
        source_file
      }
    ]
  }
]
```

따라서:

```text
FAQ item 1개
→ Document 1개
```

를 기본으로 한다.

### content 권장 구성

```text
Question: {question}

Answer:
{answers[0].answer}

[복수 answer가 있으면 같은 chunk 내 순서대로 추가]
```

### metadata

```text
document_type = "faq"
document_name = "직업능력심사평가원 FAQ"
source_file = 원본 JSON 파일
page = answers의 page가 하나로 특정될 때 해당 값
section = category
article = null
year = 원문에서 명확하지 않으면 null
```

주의:

- `answer_count > 1`인 경우 answer를 임의로 하나만 선택하지 않는다.
- answer별 source_file/page가 다르면 metadata 한 필드로 거짓 통합하지 않는다.
- MVP에서는 필요한 경우 content 안에 answer별 source/page를 함께 넣거나, answer 단위 child document로 분리하는 두 방식 중 실제 다중답변 샘플을 확인한 후 선택한다.

**LLM Schema Normalizer 불필요.**

---

## 5. 위반사례 CSV — 확정 규칙

실제 확인된 schema:

```text
위반항목
```

현재 파일은 각 행이 독립적인 위반/주의 사례 텍스트다.

따라서:

```text
1 row = 1 Document
```

### content

```text
위반항목 원문 그대로
```

### metadata

```text
document_type = "violation_case"
document_name = "직업능력심사평가원 법령 위반사항"
source_file = 원본 CSV 파일명
page = null
section = null
article = null
effective_date = null
year = 파일명에서 명확히 식별 가능한 경우에만 사용
```

중요:

- 현재 원본에 법령명, 조문번호, 위반유형 등의 별도 컬럼은 확인되지 않았다.
- 텍스트 내용을 읽어 `article`, `category` 등을 LLM이 추측하여 생성하지 않는다.
- 중복/유사 문장이 존재할 수 있으나 Phase 2 MVP에서 자동 dedup 규칙을 추가하지 않는다.

### Encoding

기존 Audit에서 CP949 주의가 기록되어 있다.

실제 구현에서는:

```python
pd.read_csv(path, encoding="cp949")
```

를 우선 시도하되, **실제 raw file에서 정상 decode 여부를 테스트로 확인한 뒤 확정**한다.

---

## 6. 법령 계열 PDF — 확정 규칙

대표 법률 샘플에서 다음 구조가 텍스트로 확인된다.

```text
[시행 YYYY. M. D.]
제1장 ...
제1조(...)
제2조(...)
...
```

따라서 MVP 법령 parser:

```text
PDF
→ page별 text
→ header/footer 정리
→ `제N조`, `제N조의N` 패턴 탐지
→ 다음 조문 직전까지 결합
→ page 범위 연결
→ Document
```

### Parser Pattern 후보

```regex
제\d+조(?:의\d+)?\(
```

단, 제목이 없는 조문이나 PDF 추출 변형 가능성을 실제 전체 문서에서 확인한 후 정규식을 최종 확정한다.

### metadata

```text
document_type
document_name
source_file
page
article
effective_date
year
section  # 장/절 추적 가능 시
```

### 반드시 처리할 것

- 한 조문이 여러 페이지에 걸치는 경우 하나의 chunk로 연결
- 페이지 header/footer 제거
- 개정 이력은 content에 원문 그대로 유지

### 하지 않을 것

- 항/호 단위까지 별도 chunk
- 법령별 개별 parser
- LLM으로 조문 경계 추정

---

## 7. 운영가이드 PDF — 확정 규칙

실제 목차에서 다음 구조가 확인된다.

```text
1부 직업능력개발훈련 제도 및 심사평가
  01 직업능력개발훈련 제도의 이해
    ① 직업능력개발훈련의 개념
    ② 직업능력개발훈련의 분야와 직종 체계
    ③ 직업능력개발훈련의 주요 구성요소

2부 고용24 행정지원시스템 사용팁 가이드
...
```

따라서 **페이지 고정 분할보다 section 기반 분할이 우선**이다.

### 권장 계층

```text
part
→ chapter
→ subsection
→ content
```

공통 Schema에는 계층 전체를 추가하지 않는다.

MVP metadata의 `section`에는 사람이 이해 가능한 경로를 문자열로 저장할 수 있다.

예:

```text
1부 > 01 직업능력개발훈련 제도의 이해 > 직업능력개발훈련의 개념
```

### fallback

section 탐지가 실패한 일부 페이지에서만 Text Splitter 사용.

---

## 8. K-Digital AI 캠퍼스 공고 — 검토 결과

실제 text extraction에서 다음이 확인된다.

```text
신청가능 직군
선정대상
지원내용
운영사항
세부 심사 계획
심사 절차
1차 심사
2차 심사
심사항목
심사문항
```

즉 `pypdf` 텍스트만으로도 핵심 의미 구조가 상당 부분 보존된다.

다만 표는 다음처럼 평탄화된다.

```text
구분 심사항목 심사문항
사업관리
사업 타당성 ...
실행 가능성 ...
```

따라서 전략:

```text
1차: pypdf
↓
심사항목 구조가 검색 가능한 수준이면 그대로 사용
↓
구조 손실이 큰 특정 페이지만 pdfplumber fallback
```

처음부터 전체 문서에 `pdfplumber`를 이중 적용하지 않는다.

### Chunking

고정 페이지 단위가 아니라:

```text
심사 신청 방법
심사 절차
1차 심사 기준
2차 심사 기준
결과 발표
...
```

같은 section/심사항목 단위를 우선한다.

---

## 9. LLM Schema Normalizer 적용 범위 — 재검토 결과

초기 아키텍처:

```text
Parser
→ Raw Content
→ LLM Schema Normalizer
→ Pydantic
```

실제 파일을 검토한 결과 **모든 문서에 LLM을 강제하는 것은 MVP에서 불필요**하다.

### LLM 불필요

```text
FAQ JSON
위반사례 CSV
법령형 PDF (조문 구조 정상 추출 시)
```

### LLM 필요 가능성

```text
가이드/보고서에서 section 구조를 규칙으로 안정적으로 매핑하지 못하는 경우
복잡한 심사 공고의 표 의미가 parser만으로 보존되지 않는 경우
```

권장 구조:

```text
Parser
→ deterministic schema mapping 가능한가?
    ├─ YES → Pydantic Validation
    └─ NO  → LLM Schema Normalizer
             → Pydantic Validation
```

이 변경은 Phase 2 구현 전 PRD와의 정합성을 다시 확인한다.

---

## 10. API 명세 PDF — RAG 범위 검토

현재 이 문서의 주요 사용처:

```text
API 필드 의미 확인
→ DATA_DICTIONARY
→ PostgreSQL Schema
```

일반 사용자가 규정/업무 질문을 할 때 검색할 Knowledge 문서로서의 가치는 낮다.

따라서 MVP 기본값:

```text
RAG 제외
```

단, 향후 사용자가 API/데이터 정의 질문도 Agent에 묻게 할 경우 추가 가능하다.

---

## 11. Chunk Size / Overlap

아직 고정하지 않는다.

구조 기반 문서:

```text
조문
FAQ 1건
위반사례 1건
section
심사항목
```

은 원 구조가 chunk boundary다.

Fallback Text Splitter를 사용할 때만:

```text
chunk_size
chunk_overlap
```

을 설정한다.

값은 Phase 2 parser 출력의 실제 길이 분포를 측정한 후 정한다.

---

## 12. Phase 2 Minimum Implementation Draft

Gate 1 PASS 후:

```text
rag/
  schema.py
  parsers.py
  chunking.py
  embeddings.py

pipeline/
  ingest_documents.py

tests/
  test_document_pipeline.py
  test_retrieval.py
```

MVP에서 추가하지 않음:

```text
generic parser framework
multi-agent
knowledge graph
upload UI
document version management
complex retry framework
```

---

## 13. Phase 2 Pre-Implementation Gate

Gate 1 PASS 후 아래 순서로 진행한다.

### P2-01 Common Schema

- [ ] Pydantic `DocumentSchema` 확정
- [ ] document_type 허용값 확정
- [ ] unknown metadata = null 검증

### P2-02 Deterministic Parser Prototype

- [ ] FAQ JSON parser
- [ ] 위반사례 CSV parser
- [ ] 대표 법령 1개 조문 parser
- [ ] 운영가이드 section parser
- [ ] K-Digital 공고 section parser

### P2-03 Parser Quality Review

- [ ] 원문 누락 여부
- [ ] chunk boundary 정확성
- [ ] page metadata 정확성
- [ ] article/section metadata 정확성
- [ ] 표 의미 손실 여부

### P2-04 결정

```text
규칙 기반 처리 충분
→ 그대로 진행

규칙 기반 처리 부족
→ 부족한 유형에만 LLM Schema Normalizer 적용
```

그 이후에만 embedding / ChromaDB로 진행한다.

---

## 14. 최종 Review

### Inventory Review: PASS

실제 대표 파일을 확인한 결과, Phase 2의 문서 유형별 처리 방향은 타당하다.

### 구현 전 보류사항

다음은 아직 확정하지 않는다.

- Chunk size / overlap
- Embedding model
- similarity threshold
- Top-K
- LLM Schema Normalizer의 최종 적용 문서
- report 문서 section parser 세부 규칙

### 가장 중요한 구현 원칙

```text
문서 구조가 이미 있으면 그 구조를 사용한다.
Parser로 가능한 일을 LLM에게 시키지 않는다.
근거 없는 metadata를 만들지 않는다.
검색 전에 원문 추적 가능성을 먼저 보장한다.
```

Phase 1 Gate 1이 PASS될 때까지 이 문서는 선행 준비 자료로만 유지한다.
