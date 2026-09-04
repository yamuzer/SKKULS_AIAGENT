# SmartHRD Phase 1 — Data Quality & SQL Validation Spec

- **Version:** v1.1
- **Status:** Phase 1 implementation specification
- **PRD:** `SmartHRD_AI_Agent_PRD_v1.3.md`
- **Scope:** `training_courses` 중심의 ETL/Data Quality 검증 + 핵심 SQL Test Set
- **Purpose:** NCS Master 작업과 병렬로 준비하며, PostgreSQL 적재 및 Gate 1 검증 기준으로 사용

---

## 1. 목적

이 문서는 Phase 1에서 다음 두 가지를 구현 기준으로 고정한다.

1. CSV → PostgreSQL ETL이 잘못된 데이터를 조용히 적재하지 않도록 Data Quality Rule을 정의한다.
2. PostgreSQL 적재 후 LLM 없이 핵심 시장지표를 정확하게 계산할 수 있는지 SQL Test Set으로 검증한다.

새로운 기능을 추가하는 문서가 아니다.

---

## 2. Validation Severity

검증 결과는 세 수준으로 구분한다.

| Level | 의미 | 처리 |
|---|---|---|
| `ERROR` | 데이터 식별/적재 신뢰성을 깨뜨림 | Load 중단 |
| `WARN` | 적재는 가능하지만 분석 시 주의 필요 | Load 허용 + 로그 |
| `INFO` | 데이터 현황 파악 목적 | Load 허용 + 로그 |

MVP에서는 복잡한 Rule Engine을 만들지 않는다.

Python ETL에서 각 검증 결과를 단순한 구조로 기록한다.

```text
rule_name
severity
passed
invalid_count
total_count
sample_values
message
```

---

## 3. Pre-load Data Quality Rules

### 3.1 Schema

| Rule ID | 검증 | 조건 | Severity |
|---|---|---|---|
| `SCHEMA_001` | 필수 원본 컬럼 | 정의된 23개 원본 컬럼의 누락 여부 | ERROR |
| `SCHEMA_002` | 업무 컬럼 | `index` 제거 후 정의된 22개 업무 컬럼 존재 | ERROR |
| `SCHEMA_003` | 예상 외 컬럼 | 신규/미정의 컬럼 존재 여부 | WARN |

> 컬럼 **순서 자체는 통과 조건으로 사용하지 않는다.** 컬럼명 집합(set)을 기준으로 검증한다.

예상 원본 컬럼:

```text
index
eiEmplRate6
eiEmplCnt3
eiEmplRate3
title
realMan
telNo
stdgScor
traStartDate
ncsCd
regCourseMan
trprDegr
address
traEndDate
subTitle
trprId
yardMan
courseMan
trainTarget
trainstCstId
subTitleLink
titleLink
wkendSe
```

---

### 3.2 Duplicate / Primary Key

| Rule ID | 검증 | 조건 | Severity |
|---|---|---|---|
| `KEY_001` | `trpr_id` NULL | 0건 | ERROR |
| `KEY_002` | `trpr_degr` NULL | 0건 | ERROR |
| `KEY_003` | 복합 PK 중복 | `(trpr_id, trpr_degr)` 중복 0건 | ERROR |
| `DUP_001` | 완전중복 | `index` 제외 완전중복 수 기록 | INFO |

처리 순서:

```text
index 제거
→ 업무 컬럼 기준 완전중복 제거
→ PK NULL/중복 검증
```

기존 profiling 기준 기대값:

```text
원본 행 수            628,384
완전중복              8,847
중복 제거 후          619,537
PK 중복               0
PK NULL                0
```

위 숫자는 ETL 결과와 대조할 reference이며,
새 데이터가 들어오면 하드코딩된 통과 조건으로 사용하지 않는다.

---

### 3.3 Type Conversion

| Rule ID | 대상 | 검증 | Severity |
|---|---|---|---|
| `TYPE_001` | `trpr_degr` | **원본 non-null 값**의 INTEGER 변환 실패 | ERROR |
| `TYPE_002` | 날짜 2개 | **원본 non-null 값**의 DATE 변환 실패 | ERROR |
| `TYPE_003` | 인원 필드 | **원본 non-null 값**의 INTEGER 변환 실패 | ERROR |
| `TYPE_004` | 금액 필드 | **원본 non-null 값**의 BIGINT 변환 실패 | ERROR |
| `TYPE_005` | 점수/취업률 | **원본 non-null 값**의 NUMERIC 변환 실패 | WARN |
| `TYPE_006` | ID/Code | 문자열 보존 여부 | ERROR |

> **원본 NULL과 타입 변환 실패는 구분한다.** 현재 `NOT NULL` 여부가 최종 확정되지 않은 필드의 NULL 자체를 타입 오류로 처리하지 않는다.

대상 그룹:

```text
DATE
- tra_start_date
- tra_end_date

INTEGER
- trpr_degr
- reg_course_man
- yard_man
- ei_empl_cnt_3

BIGINT
- course_man
- real_man

NUMERIC
- stdg_scor
- ei_empl_rate_3
- ei_empl_rate_6

STRING / CODE
- trpr_id
- trainst_cst_id
- ncs_cd
- tel_no
- wkend_se
```

---

### 3.4 Logical Validity

| Rule ID | 검증 | 기준 | Severity |
|---|---|---|---|
| `LOGIC_001` | 훈련기간 | `tra_end_date >= tra_start_date` | WARN |
| `LOGIC_002` | 정원 | `yard_man >= 0` | WARN |
| `LOGIC_003` | 신청인원 | `reg_course_man >= 0` | WARN |
| `LOGIC_004` | 취업인원 | `ei_empl_cnt_3 >= 0` 또는 NULL | WARN |
| `LOGIC_005` | 수강비 | `course_man >= 0` | WARN |
| `LOGIC_006` | 실제훈련비 | `real_man >= 0` | WARN |

이상치를 자동 삭제하거나 보정하지 않는다.

로그를 남기고 원본을 확인한다.

---

### 3.5 NCS Code

| Rule ID | 검증 | 기준 | Severity |
|---|---|---|---|
| `NCS_001` | float 표현 | `.0`으로 끝나는 코드 수 기록 | INFO |
| `NCS_002` | 코드 정규화 | `.0` 제거 후 문자열 보존 | ERROR |
| `NCS_003` | 임의 padding | `zfill()` 등 추정 기반 보정 금지 | ERROR |
| `NCS_004` | NULL | NULL 건수/비율 기록 | INFO |
| `NCS_005` | Master 매칭 | 과정 기준/코드 기준 매칭률 계산 | WARN |

NCS Master 생성 이후 다음 지표를 출력한다.

```text
total_course_runs
ncs_non_null_course_runs
unique_ncs_codes
matched_course_runs
unmatched_course_runs
course_run_match_rate
matched_unique_codes
unmatched_unique_codes
unique_code_match_rate
```

FK는 매칭률과 미매칭 원인을 확인하기 전 강제하지 않는다.

---

### 3.6 Nullable Performance Fields

대상:

```text
stdg_scor
ei_empl_cnt_3
ei_empl_rate_3
ei_empl_rate_6
```

규칙:

- NULL을 `0`으로 변환하지 않는다.
- 평균 산출 시 SQL의 NULL 제외 동작을 이용한다.
- Agent용 분석에서는 평균값만 반환하지 않고 가능한 경우 coverage를 함께 반환한다.

Coverage:

```sql
COUNT(target_column)::numeric / NULLIF(COUNT(*), 0)
```

---

### 3.7 Weekend Code

허용 코드:

```text
0 = 해당없음
1 = 주말
2 = 주말·주중 혼합
3 = 주중
NULL = 정보 없음
```

| Rule ID | 검증 | 기준 | Severity |
|---|---|---|---|
| `CODE_001` | `wkend_se` | `{0,1,2,3,NULL}` 외 값 탐지 | WARN |

DB에는 문자열 코드로 저장한다.

---

## 4. Post-load PostgreSQL Verification

Load 완료 후 아래 검증을 SQL로 다시 수행한다.

### V01. 전체 개설 회차 수

```sql
SELECT COUNT(*) AS course_run_count
FROM training_courses;
```

중복 제거된 ETL 출력 행 수와 같아야 한다.

### V02. PK NULL

```sql
SELECT COUNT(*) AS invalid_count
FROM training_courses
WHERE trpr_id IS NULL
   OR trpr_degr IS NULL;
```

기대:

```text
0
```

### V03. PK 중복

```sql
SELECT COUNT(*) AS duplicate_key_count
FROM (
    SELECT trpr_id, trpr_degr
    FROM training_courses
    GROUP BY trpr_id, trpr_degr
    HAVING COUNT(*) > 1
) x;
```

기대:

```text
0
```

### V04. 기간 이상치

```sql
SELECT COUNT(*) AS invalid_date_range_count
FROM training_courses
WHERE tra_start_date IS NOT NULL
  AND tra_end_date IS NOT NULL
  AND tra_end_date < tra_start_date;
```

0이 아닐 경우 삭제하지 않고 샘플을 확인한다.

### V05. NCS NULL

```sql
SELECT
    COUNT(*) AS total_count,
    COUNT(ncs_cd) AS ncs_non_null_count,
    COUNT(*) - COUNT(ncs_cd) AS ncs_null_count
FROM training_courses;
```

### V06. 주요 NULL Coverage

```sql
SELECT
    COUNT(*) AS total_count,
    COUNT(stdg_scor) AS stdg_scor_count,
    COUNT(ei_empl_cnt_3) AS ei_empl_cnt_3_count,
    COUNT(ei_empl_rate_3) AS ei_empl_rate_3_count,
    COUNT(ei_empl_rate_6) AS ei_empl_rate_6_count
FROM training_courses;
```

---

## 5. Core SQL Test Set

목적은 Text-to-SQL 테스트가 아니라
**PostgreSQL 데이터와 Semantic Metric 자체가 정확한지 검증**하는 것이다.

### T01. 전체 고유 과정 수

사용자 질문:

```text
전체 훈련과정은 몇 개야?
```

Metric:

```text
course_count
```

SQL:

```sql
SELECT COUNT(DISTINCT trpr_id) AS course_count
FROM training_courses;
```

---

### T02. 전체 개설 회차 수

사용자 질문:

```text
전체 개설 회차는 몇 개야?
```

Metric:

```text
course_run_count
```

SQL:

```sql
SELECT COUNT(*) AS course_run_count
FROM training_courses;
```

**T01과 T02를 동일하게 처리하면 실패다.**

또한 `course_count = COUNT(DISTINCT trpr_id)`는 차원별 집계에서 **비가산(non-additive) 지표**다.
예를 들어 하나의 `trpr_id`가 서로 다른 기간/NCS 그룹에 등장할 수 있으므로,
그룹별 `course_count`를 단순 합산하여 전체 `course_count`로 사용하지 않는다.

---

### T03. 기간별 개설 추이

사용자 질문:

```text
연도별 훈련과정 개설 추이를 보여줘.
```

SQL 기준:

```sql
SELECT
    EXTRACT(YEAR FROM tra_start_date)::int AS year,
    COUNT(DISTINCT trpr_id) AS course_count,
    COUNT(*) AS course_run_count
FROM training_courses
WHERE tra_start_date IS NOT NULL
GROUP BY 1
ORDER BY 1;
```

---

### T04. 지역별 과정/회차 현황

현재 Region Master가 없으므로 `address` 원문 기반이다.

사용자 질문:

```text
서울 지역 훈련과정은 몇 개야?
```

MVP SQL 예:

```sql
SELECT
    COUNT(DISTINCT trpr_id) AS course_count,
    COUNT(*) AS course_run_count
FROM training_courses
WHERE address LIKE '서울%';
```

주의:

- 현재는 주소 문자열 기반 임시 분석이다.
- 정확한 행정구역 분석은 Region Master 도입 이후 개선한다.

---

### T05. NCS 세분류별 시장 규모

NCS Master 적재 후:

```sql
SELECT
    t.ncs_cd,
    n.detail_name,
    COUNT(DISTINCT t.trpr_id) AS course_count,
    COUNT(*) AS course_run_count
FROM training_courses t
LEFT JOIN ncs_codes n
  ON t.ncs_cd = n.detail_code
GROUP BY t.ncs_cd, n.detail_name
ORDER BY course_run_count DESC;
```

`detail_name IS NULL`인 행은 제거하지 않는다.  
이 행들은 `ncs_cd` NULL 또는 Master 미매칭 데이터이므로 NCS 매칭 품질을 함께 보여준다.

---

### T06. NCS 대분류별 시장 규모

```sql
SELECT
    n.major_code,
    n.major_name,
    COUNT(DISTINCT t.trpr_id) AS course_count,
    COUNT(*) AS course_run_count
FROM training_courses t
LEFT JOIN ncs_codes n
  ON t.ncs_cd = n.detail_code
GROUP BY n.major_code, n.major_name
ORDER BY course_run_count DESC;
```

`major_code IS NULL` 그룹은 삭제하지 않는다.  
이는 NCS NULL 또는 Master 미매칭 과정 회차이며, 전체 대비 규모를 확인할 수 있어야 한다.

---

### T07. 기관별 개설 현황

사용자 질문:

```text
개설 회차가 많은 훈련기관을 알려줘.
```

```sql
SELECT
    trainst_cst_id,
    COUNT(DISTINCT trpr_id) AS course_count,
    COUNT(*) AS course_run_count
FROM training_courses
GROUP BY trainst_cst_id
ORDER BY course_run_count DESC;
```

주의:

`sub_title`의 공식 정의는 '부 제목'이므로 **기관 집계의 GROUP BY 키로 사용하지 않는다.**
기관 식별 기준은 `trainst_cst_id`다.

추후 `sub_title`이 실제 기관명으로 안정적으로 대응하는지 검증되면 표시용 label로만 사용할 수 있다.

---

### T08. 평균 만족도 + Coverage

사용자 질문:

```text
훈련과정 평균 만족도는 어때?
```

```sql
SELECT
    AVG(stdg_scor) AS avg_stdg_scor,
    COUNT(stdg_scor) AS valid_count,
    COUNT(*) AS total_count,
    COUNT(stdg_scor)::numeric / NULLIF(COUNT(*), 0) AS coverage
FROM training_courses;
```

평균만 단독 반환하지 않는다.

---

### T09. 6개월 취업률 + Coverage

사용자 질문:

```text
평균 6개월 취업률이 높은 NCS 분야는 어디야?
```

```sql
SELECT
    n.detail_code,
    n.detail_name,
    AVG(t.ei_empl_rate_6) AS avg_ei_empl_rate_6,
    COUNT(t.ei_empl_rate_6) AS valid_count,
    COUNT(*) AS total_count,
    COUNT(t.ei_empl_rate_6)::numeric / NULLIF(COUNT(*), 0) AS coverage
FROM training_courses t
LEFT JOIN ncs_codes n
  ON t.ncs_cd = n.detail_code
WHERE n.detail_code IS NOT NULL
GROUP BY n.detail_code, n.detail_name;
```

최종 정렬/최소 표본 조건은 실제 coverage 분포를 본 뒤 확정한다.
MVP 단계에서 임의 threshold를 만들지 않는다.

---

### T10. 정원 대비 신청 인원

사용자 질문:

```text
정원 대비 신청이 많은 과정은 어떤 과정이야?
```

```sql
SELECT
    trpr_id,
    trpr_degr,
    title,
    reg_course_man,
    yard_man,
    reg_course_man::numeric / NULLIF(yard_man, 0) AS application_ratio
FROM training_courses
WHERE reg_course_man IS NOT NULL
  AND yard_man IS NOT NULL
ORDER BY application_ratio DESC NULLS LAST;
```

`yard_man = 0`은 분모에서 제외한다.

---

## 6. Reference Reconciliation

PostgreSQL 적재 후 반드시 세 층을 대조한다.

```text
Raw CSV
   ↓
Cleaned DataFrame
   ↓
PostgreSQL
```

최소 대조 지표:

| Metric | Raw | Cleaned | PostgreSQL |
|---|---:|---:|---:|
| 원본 행 수 | 확인 | - | - |
| 완전중복 수 | 확인 | 제거 | - |
| `course_run_count` | - | 확인 | 동일해야 함 |
| `course_count` | 확인 | 확인 | 동일해야 함 |
| PK 중복 | 확인 | 0 | 0 |
| PK NULL | 확인 | 0 | 0 |
| NCS NULL | 확인 | 동일 | 동일 |
| 주요 성과필드 non-null 수 | 확인 | 동일 | 동일 |

숫자가 다르면 PostgreSQL 쿼리를 수정하기 전에
**어느 단계에서 행 또는 값이 바뀌었는지 먼저 확인한다.**

---

## 7. ETL Log Minimum Output

한 번의 ETL 실행에서 최소 다음 정보를 남긴다.

```text
run_started_at
source_file
source_row_count
source_column_count
exact_duplicate_count
cleaned_row_count
pk_null_count
pk_duplicate_count
type_conversion_errors
validation_warnings
loaded_row_count
load_status
run_finished_at
```

MVP에서는 별도 로그 DB/Table을 먼저 만들 필요가 없다.

초기에는 콘솔 + 파일 로그(JSON 또는 text)면 충분하다.

---

## 8. Gate 1 Acceptance Criteria

Phase 1 Structured Data Foundation은 아래를 모두 만족하면 통과한다.

- [ ] CSV 23개 컬럼과 Data Dictionary가 일치한다.
- [ ] `index`가 제거된다.
- [ ] 완전중복 제거가 재현 가능하다.
- [ ] `(trpr_id, trpr_degr)` NULL = 0
- [ ] `(trpr_id, trpr_degr)` 중복 = 0
- [ ] ID/Code/Date/Numeric 변환 규칙이 재현 가능하다.
- [ ] NCS 4단계 Master가 생성된다.
- [ ] NCS 과정 기준/코드 기준 매칭률이 계산된다.
- [ ] 미매칭 NCS 코드가 확인된다.
- [ ] PostgreSQL 적재 행 수가 cleaned DataFrame과 일치한다.
- [ ] `course_count`와 `course_run_count`가 구분된다.
- [ ] 기간/지역/NCS별 핵심 SQL이 실행된다.
- [ ] 성과지표 분석 시 NULL coverage가 확인된다.
- [ ] 원본 → DataFrame → PostgreSQL 핵심 지표가 대조 검증된다.
- [ ] ETL 재실행 시 동일 입력에 동일 결과를 생성한다.

---

## 9. Codex 구현 시 전달사항

Codex에는 이 문서와 `DATA_DICTIONARY.md`를 함께 제공한다.

구현 원칙:

1. Validation 코드는 ETL과 분리된 함수 수준이면 충분하다.
2. 별도 validation framework를 도입하지 않는다.
3. 이상치를 자동 수정/삭제하지 않는다.
4. ERROR는 Load 중단, WARN은 로그 후 진행한다.
5. NCS 미매칭은 Load 실패 조건이 아니다.
6. SQL Test Set은 pytest 또는 간단한 verification script로 실행 가능하게 만든다.
7. 테스트용 복잡한 Mock 인프라를 만들지 않는다.
8. 모든 지표는 PostgreSQL 결과와 원본/cleaned 결과를 대조할 수 있어야 한다.

---

## 10. v1.1 재검토 반영사항

구현 전 2차 검토에서 다음을 수정했다.

1. **원본 NULL과 타입 변환 실패를 분리**
   - nullable 필드의 결측값을 타입 오류로 오판하지 않도록 수정
2. **Schema 검증은 컬럼 순서가 아닌 컬럼명 집합 기준**
   - CSV 컬럼 순서 변경으로 불필요하게 ETL이 실패하지 않도록 수정
3. **기관별 집계 키 수정**
   - `sub_title`을 GROUP BY에서 제거하고 `trainst_cst_id`만 기관 식별자로 사용
4. **NCS 시장 집계에서 미매칭 데이터 보존**
   - `INNER JOIN` 대신 `LEFT JOIN`을 사용하여 NCS NULL/미매칭 과정이 조용히 사라지지 않도록 수정
5. **`course_count`의 비가산성 명시**
   - 그룹별 `COUNT(DISTINCT trpr_id)` 합계를 전체 고유 과정 수로 오용하지 않도록 명시

이 다섯 항목은 기능 확장이 아니라 데이터 분석 정확성을 위한 보정이다.

---

## 11. 다음 합류 지점

현재 병렬 작업:

```text
Agent
NCS Master 추출
→ NCS Matching 분석
        ↓

이 문서
DQ Rules
→ SQL Test Set
        ↓

합류
NCS 결과 검토
→ training_courses + ncs_codes Schema 최종 확정
→ PostgreSQL DDL / ETL 구현 명세
→ Codex 구현
```

NCS 결과가 나오기 전까지 LangGraph, RAG Retrieval, Streamlit,
Region Master를 추가 설계하지 않는다.
