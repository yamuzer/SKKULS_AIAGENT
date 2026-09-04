# SmartHRD AI Agent — Database Design Document (Phase 0)

- **Date:** 2026-09-04
- **Status:** Complete (Phase 0 Deliverable)
- **Author:** Antigravity (Advanced Agentic Assistant)
- **Target DB:** PostgreSQL (Recommended version: 15+)
- **Scope:** Phase 1 Structured Foundation Schema & Analysis SQL

---

## 1. 개요 및 설계 원칙

본 문서는 SmartHRD AI Agent의 정형 데이터 저장소인 **PostgreSQL 스키마 및 인덱스, 지표 산출 쿼리**를 정의한다.
PRD v1.3 및 `DATA_AUDIT.md`의 전수 프로파일링 결과를 직접 반영하여 수립되었다.

### 핵심 설계 원칙
1. **Source of Truth:** 정형 시장 지표(과정 수, 개설 회차 수, 수강료, 인원, 성과)는 LLM의 추정이 아닌 PostgreSQL에서만 계산한다.
2. **Fact 단일 테이블 모델링:** 불필요한 차원(Dimension) 분리(기관, 지역 등)는 MVP 단계에서 지양하고, `training_courses` 단일 Fact 테이블을 유지하여 쿼리 복잡성을 낮춘다.
3. **Soft Foreign Key 원칙:** 2022년 NCS Master 대비 2026년 훈련과정의 3.68%가 신설/개편 코드로 미매칭되므로, Hard FK 제약 대신 인덱스가 부여된 논리적 외래키와 `LEFT JOIN` 구조를 적용한다.
4. **결측치 왜곡 방지:** 취업률 등 90% 결측 지표는 0으로 치환하지 않고 `NULL`을 유지하며, 집계 시 유효 모수(커버리지)를 반드시 계산한다.

---

## 2. DDL 스키마 정의

### 2.1 NCS 분류 Master 테이블 (`ncs_codes`)

NCS 2022 마스터 엑셀에서 추출한 1,083개 세분류(8자리) 마스터 테이블.

```sql
CREATE TABLE IF NOT EXISTS ncs_codes (
    detail_cd       VARCHAR(8)      NOT NULL,
    detail_nm       TEXT            NOT NULL,
    major_cd        VARCHAR(2)      NOT NULL,
    major_nm        TEXT            NOT NULL,
    mid_cd          VARCHAR(2)      NOT NULL,
    mid_nm          TEXT            NOT NULL,
    minor_cd        VARCHAR(2)      NOT NULL,
    minor_nm        TEXT            NOT NULL,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_ncs_codes PRIMARY KEY (detail_cd)
);

CREATE INDEX idx_ncs_major_cd ON ncs_codes (major_cd);
CREATE INDEX idx_ncs_mid_cd   ON ncs_codes (mid_cd);
CREATE INDEX idx_ncs_minor_cd ON ncs_codes (minor_cd);
```

### 2.2 훈련과정 Fact 테이블 (`training_courses`)

국민내일배움카드 훈련과정 619,537건(중복 제거 후)을 적재하는 핵심 공급(Supply) 테이블.

```sql
CREATE TABLE IF NOT EXISTS training_courses (
    -- 복합 기본키 (PK)
    trpr_id           VARCHAR(50)     NOT NULL,
    trpr_degr         INTEGER         NOT NULL,

    -- 과정 및 기관 정보
    title             TEXT            NOT NULL,
    sub_title         TEXT            NOT NULL,  -- 부 제목 (공식 API 명칭). 기관 식별 Key 아님
    trainst_cst_id    VARCHAR(50)     NOT NULL,  -- 훈련기관 ID (기관 유일 식별자 및 GROUP BY Key)

    -- 일정 및 위치
    tra_start_date    DATE            NOT NULL,
    tra_end_date      DATE            NOT NULL,
    address           TEXT            NOT NULL,  -- 시군구 수준 주소

    -- 분류 및 대상
    ncs_cd            VARCHAR(8),                -- 8자리 정규화된 NCS 코드 (Soft FK)
    train_target      TEXT            NOT NULL,  -- 훈련대상 구분
    wkend_se          VARCHAR(10),               -- 주말/주중 구분 ('0', '1', '2', '3', '9')

    -- 비용 및 정원/인원 지표
    real_man          BIGINT          NOT NULL,  -- 실제 훈련비 (원)
    course_man        BIGINT          NOT NULL,  -- 수강비 (원)
    reg_course_man    INTEGER         NOT NULL,  -- 수강신청 인원
    yard_man          INTEGER         NOT NULL,  -- 정원

    -- 성과 및 만족도 지표 (결측 허용)
    stdg_scor         NUMERIC(5,2)    NOT NULL,  -- 만족도 점수 (0.0 ~ 100.0)
    ei_empl_rate_3    NUMERIC(6,3),              -- 3개월 고용보험 취업률 (%)
    ei_empl_rate_6    NUMERIC(6,3),              -- 6개월 고용보험 취업률 (%)
    ei_empl_cnt_3     INTEGER,                   -- 3개월 고용보험 취업자 수

    -- 연락처 및 링크
    tel_no            VARCHAR(50),
    title_link        TEXT            NOT NULL,
    sub_title_link    TEXT            NOT NULL,

    created_at        TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_training_courses PRIMARY KEY (trpr_id, trpr_degr)
);
```

---

## 3. 인덱스 전략 (Indexing Strategy)

에이전트가 자주 실행하는 대표 쿼리 패턴(기간, 지역, NCS, 기관명)의 성능을 보장하기 위해 인덱스를 구성한다.

```sql
-- 1. 기간 기반 조회 및 추이 분석
CREATE INDEX idx_tc_start_date ON training_courses (tra_start_date);
CREATE INDEX idx_tc_end_date   ON training_courses (tra_end_date);

-- 2. 직종(NCS) 기반 필터 및 JOIN 최적화
CREATE INDEX idx_tc_ncs_cd ON training_courses (ncs_cd);

-- 3. 지역(Address) 조건 검색
CREATE INDEX idx_tc_address ON training_courses (address);

-- 4. 훈련기관별 과정 집계 및 검색
CREATE INDEX idx_tc_sub_title ON training_courses (sub_title);
CREATE INDEX idx_tc_trainst_id ON training_courses (trainst_cst_id);

-- 5. 복합 조건 (지역 + 시작일)
CREATE INDEX idx_tc_address_start ON training_courses (address, tra_start_date);
```

---

## 4. 핵심 시맨틱 메트릭 (Semantic Metrics) 및 표준 SQL

PRD 3.1절 및 5절, `PHASE1_VALIDATION_SPEC_v1.1.md`에 정의된 에이전트 핵심 시장분석 지표를 산출하는 표준 SQL 쿼리 템플릿이다.

### 4.1 기본 지표: 과정 수 vs 개설 회차 수

```sql
-- 특정 지역/직종에 대한 시장 개요
SELECT
    COUNT(DISTINCT tc.trpr_id)        AS course_count,      -- 고유 과정 수
    COUNT(*)                          AS course_run_count,  -- 개설 회차 수
    COUNT(DISTINCT tc.trainst_cst_id) AS inst_count,        -- 운영 기관 수
    ROUND(AVG(tc.real_man), 0)        AS avg_real_man,      -- 평균 실제훈련비
    ROUND(AVG(tc.course_man), 0)      AS avg_course_man,    -- 평균 수강비
    ROUND(AVG(tc.stdg_scor), 1)       AS avg_satisfaction   -- 평균 만족도 점수
FROM training_courses tc
WHERE tc.address LIKE '%용인%'
  AND tc.tra_start_date >= '2024-01-01';
```

> **`course_count` 비가산성(Non-additive) 원칙:**  
> `course_count = COUNT(DISTINCT trpr_id)`는 비가산 지표다. 하위 그룹별(예: 지역별, NCS별) course_count를 단순 합산하여 상위/전체 course_count를 계산하면 왜곡이 발생하므로, 전체 과정 수가 필요할 때는 반드시 원본 Fact에서 `COUNT(DISTINCT trpr_id)`를 직접 재계산한다.

### 4.2 NCS 대분류 결합 지표 (Soft FK 및 LEFT JOIN 원칙)

Master 미매칭 데이터(3.69%)가 분석에서 누락되지 않도록 반드시 `LEFT JOIN`을 사용한다.

```sql
SELECT
    COALESCE(n.major_nm, 'NCS Master 미매칭')  AS ncs_major,
    COUNT(DISTINCT tc.trpr_id)                AS course_count,
    COUNT(*)                                  AS course_run_count,
    ROUND(AVG(tc.real_man), 0)                AS avg_real_man
FROM training_courses tc
LEFT JOIN ncs_codes n ON tc.ncs_cd = n.detail_cd
WHERE tc.address LIKE '%용인%'
GROUP BY COALESCE(n.major_nm, 'NCS Master 미매칭')
ORDER BY course_count DESC;
```

### 4.3 훈련기관별 집계 지표 (단독 trainst_cst_id GROUP BY 원칙)

훈련기관 식별 기준은 `trainst_cst_id`이며, 동일 기관이 분리 집계되지 않도록 `GROUP BY trainst_cst_id, sub_title` 복합 그룹화를 금지한다.

```sql
SELECT
    tc.trainst_cst_id,
    MAX(tc.sub_title)                 AS sample_sub_title,  -- 화면 표시용 라벨 (Key 아님)
    COUNT(DISTINCT tc.trpr_id)        AS course_count,
    COUNT(*)                          AS course_run_count
FROM training_courses tc
GROUP BY tc.trainst_cst_id
ORDER BY course_run_count DESC;
```

### 4.4 취업률 성과 지표 (결측 모수 표기 원칙 준수)

```sql
-- 취업률을 단순 평균내지 않고, 성과 데이터가 존재하는 유효 모수(커버리지)를 함께 집계
SELECT
    COUNT(*)                                                        AS total_runs,
    COUNT(tc.ei_empl_rate_3)                                        AS rated_runs_3m,
    ROUND((COUNT(tc.ei_empl_rate_3)::numeric / NULLIF(COUNT(*), 0)) * 100, 1) AS coverage_rate_3m_pct,
    ROUND(AVG(tc.ei_empl_rate_3), 1)                                AS avg_empl_rate_3m,
    ROUND(AVG(tc.ei_empl_rate_6), 1)                                AS avg_empl_rate_6m
FROM training_courses tc
WHERE tc.address LIKE '%용인%'
  AND tc.ncs_cd LIKE '20%';  -- 정보통신 대분류
```

---

## 5. ETL 파이프라인 정규화 및 적재 절차

```text
[Raw CSV] 
   │
   ├─ Step 1: index 컬럼 드롭
   ├─ Step 2: 22개 업무 컬럼 집합(Set) 기준 완전 중복 제거 (8,847건 제거 -> 619,537건)
   ├─ Step 3: ncsCd 정규화 (문자열 변환 -> .0 제거 -> 8자리 미만 유효 코드 zfill(8))
   ├─ Step 4: 날짜/숫자형 타입 변환 (Date, BigInt, Numeric)
   ├─ Step 5: wkendSe 결측은 NULL, 9.0은 '9'(공식 명세 미확인 코드)로 보존
   ├─ Step 6: Python / pandas 기반 단순 유효성 검증 (ERROR / WARN / INFO 로그, 불필요한 Pandera 배제)
   │
[PostgreSQL COPY / Bulk Insert]
   │
[SQL Assertion 검증: 619,537건 일치 여부 확인]
```

### 검증 규칙
* **Schema Validation:** 컬럼 순서에 의존하지 않고, 정의된 22개 업무 컬럼 집합(Set) 존재 여부로 검증.
* **타입 변환 에러 분리:** 원본 NULL과 원본 non-null의 타입 변환 실패(`original_not_null AND converted_is_null`)를 엄격히 분리.
* **Severity 3단계:**
  - `ERROR`: PK NULL, PK 중복, 필수 컬럼 누락, 필수 타입 변환 실패 $\rightarrow$ Load 즉시 중단.
  - `WARN`: 날짜 역전, 비정상 범위, NCS 미매칭, 미확인 코드(9) $\rightarrow$ 로그 후 적재 계속.
  - `INFO`: 중복 제거 수, 매칭률, Coverage 현황 $\rightarrow$ 로그 기록.

### 검증 체크리스트
- [ ] 적재 후 총 행 수가 정확히 619,537건인가?
- [ ] `(trpr_id, trpr_degr)` 중복이 0건인가?
- [ ] `ncs_codes` 마스터 1,083건이 정상 적재되었는가?
- [ ] `training_courses.ncs_cd` 매칭률이 96.31% (596,177건) 수준으로 일치하는가?
