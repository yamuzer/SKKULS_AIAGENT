# SmartHRD AI Agent — Gate 1 Review Checklist

- **Version:** v1.0
- **Scope:** Phase 1 — Structured Data Foundation
- **Purpose:** Phase 1 구현 완료 후 Gate 1 통과 여부를 빠르게 판정하기 위한 검토 체크리스트
- **Source of Truth:** `SmartHRD_AI_Agent_PRD_v1.3.md`
- **Related Specs:** `DATA_DICTIONARY.md`, `DATABASE_DESIGN.md`, `PHASE1_VALIDATION_SPEC_v1.1.md`, `NCS_MATCHING_REPORT.md`

---

## 1. Gate 1 판정 원칙

Gate 1은 **PostgreSQL에 적재되었다는 사실만으로 통과하지 않는다.**

다음 4가지를 모두 만족해야 한다.

1. 데이터가 정확히 적재되었다.
2. 핵심 Data Quality Rule을 통과했다.
3. LLM 없이 SQL로 핵심 시장지표를 계산할 수 있다.
4. Raw → Cleaned → PostgreSQL 결과가 서로 일치한다.

최종 판정:

```text
PASS
또는
FIX REQUIRED
```

부분 통과는 기록할 수 있지만 전체 Gate 1은 위 조건을 모두 만족해야 PASS다.

---

## 2. Environment Check

파일럿 환경 기준:

- [ ] PostgreSQL이 localhost에서 정상 실행된다.
- [ ] `smarthrd` DB에 접속 가능하다.
- [ ] `.env`를 통해 DB 접속정보를 읽는다.
- [ ] DB 비밀번호가 코드에 하드코딩되어 있지 않다.
- [ ] Docker / Alembic / ORM / 별도 Validation Framework를 추가하지 않았다.

### 최소 확인

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthrd
```

---

## 3. Schema Check

### `ncs_codes`

- [ ] 총 1,083건 적재
- [ ] `detail_cd`가 PK
- [ ] 코드 컬럼은 문자열
- [ ] `detail_cd`는 8자리 문자열 기준
- [ ] Hard FK 없음

### `training_courses`

- [ ] 업무 컬럼 22개가 적재됨
- [ ] `(trpr_id, trpr_degr)` 복합 PK 적용
- [ ] `trpr_id`는 문자열
- [ ] `trainst_cst_id`는 문자열
- [ ] `ncs_cd`는 `VARCHAR(8)`
- [ ] 날짜 컬럼은 `DATE`
- [ ] 인원은 `INTEGER`
- [ ] 금액은 `BIGINT`
- [ ] 취업률/만족도는 `NUMERIC`
- [ ] nullable 성과필드는 NULL 유지

---

## 4. Row Count & Duplicate Check

공식 기준값:

| Metric | Expected |
|---|---:|
| Raw rows | 628,384 |
| Exact duplicates | 8,847 |
| Cleaned rows / `course_run_count` | 619,537 |
| `course_count` | 139,138 |
| PK NULL | 0 |
| PK duplicate | 0 |

검토:

- [ ] 원본 행 수 = 628,384
- [ ] `index` 제외 완전중복 = 8,847
- [ ] 정제 후 행 수 = 619,537
- [ ] PostgreSQL `COUNT(*)` = 619,537
- [ ] `COUNT(DISTINCT trpr_id)` = 139,138
- [ ] PK NULL = 0
- [ ] PK duplicate = 0

---

## 5. NCS Normalization Check

확정 ETL 규칙:

```text
NULL
→ NULL 유지

non-null
→ 문자열 변환
→ trailing ".0" 제거
→ 8자리 미만 유효 코드 zfill(8)
→ VARCHAR(8)
```

검토:

- [ ] `.0`이 제거된다.
- [ ] 선행 0 복원이 적용된다.
- [ ] 비정상 형식을 임의 수정하지 않는다.
- [ ] Master 미매칭 코드를 임의 변경하지 않는다.
- [ ] 미매칭 데이터도 `training_courses`에 적재된다.
- [ ] NCS 분석은 `LEFT JOIN`을 기본으로 한다.

---

## 6. NCS Matching Check

공식 기준값:

| Metric | Expected |
|---|---:|
| total_course_runs | 619,537 |
| ncs_non_null_course_runs | 619,029 |
| matched_course_runs | 596,177 |
| unmatched_course_runs | 22,852 |
| course_run_match_rate | 96.31% |
| unique_ncs_codes | 584 |
| matched_unique_codes | 528 |
| unmatched_unique_codes | 56 |
| unique_code_match_rate | 90.41% |

검토:

- [ ] 위 9개 지표가 재현된다.
- [ ] Hard FK를 적용하지 않았다.
- [ ] 미매칭을 ETL ERROR로 처리하지 않는다.
- [ ] 미매칭 label은 `NCS Master 미매칭` 등 중립 표현을 사용한다.
- [ ] “신설/개편”을 공식 확인 없이 단정하지 않는다.

---

## 7. `wkend_se` Check

공식 명세:

```text
0 = 해당없음
1 = 주말
2 = 주말·주중 혼합
3 = 주중
```

실제 데이터에 `9`가 존재한다.

검토:

- [ ] `9`는 원본 코드 그대로 보존된다.
- [ ] `9 = 기타/미지정`으로 공식 의미를 확정하지 않는다.
- [ ] UI/Agent에서 필요하면 `공식 명세 미확인 코드` 수준으로 표현한다.
- [ ] NULL을 임의 코드로 변환하지 않는다.

---

## 8. Type Conversion Check

원칙:

```text
원본 NULL != 타입 변환 실패
```

검토:

- [ ] 원본 NULL은 허용 정책에 따라 그대로 유지된다.
- [ ] non-null 값이 변환 후 NULL이 된 경우만 변환 실패로 집계한다.
- [ ] 날짜 변환 실패 건수 확인
- [ ] 인원 변환 실패 건수 확인
- [ ] 금액 변환 실패 건수 확인
- [ ] 취업률/만족도 변환 실패 건수 확인
- [ ] 변환 실패 샘플값 로그 확인

---

## 9. Logical Data Quality Check

- [ ] `tra_end_date < tra_start_date` 건수 확인
- [ ] 음수 `yard_man` 확인
- [ ] 음수 `reg_course_man` 확인
- [ ] 음수 `course_man` 확인
- [ ] 음수 `real_man` 확인
- [ ] 음수 `ei_empl_cnt_3` 확인

이상값이 있더라도 자동 삭제/보정하지 않고 로그 후 원본 확인한다.

---

## 10. Performance Metric Coverage Check

대상:

```text
ei_empl_rate_3
ei_empl_rate_6
ei_empl_cnt_3
stdg_scor
```

검토:

- [ ] NULL을 0으로 치환하지 않았다.
- [ ] 평균 계산 시 valid_count를 함께 반환한다.
- [ ] total_count를 함께 반환한다.
- [ ] coverage를 함께 반환한다.
- [ ] 임의 최소 coverage threshold를 아직 추가하지 않았다.

---

## 11. Semantic Metric Check

### `course_count`

```sql
COUNT(DISTINCT trpr_id)
```

### `course_run_count`

```sql
COUNT(*)
```

검토:

- [ ] 두 지표를 동일하게 처리하지 않는다.
- [ ] 전체 `course_count` = 139,138 재현
- [ ] 전체 `course_run_count` = 619,537 재현
- [ ] 그룹별 `course_count`를 합산해서 전체 `course_count`를 만들지 않는다.
- [ ] 전체 고유 과정 수는 Fact에서 다시 `COUNT(DISTINCT trpr_id)`로 계산한다.

---

## 12. Institution Aggregation Check

기관 식별 Key:

```text
trainst_cst_id
```

검토:

- [ ] 기관별 집계는 `GROUP BY trainst_cst_id`
- [ ] `sub_title`을 기관 식별 Key로 사용하지 않는다.
- [ ] `sub_title`은 공식 의미인 `부 제목`으로 유지한다.
- [ ] 필요할 경우 표시용 label 후보로만 사용한다.

---

## 13. T01 ~ T10 SQL Test Set

각 쿼리가 실행되는지만 보지 않고 **결과 의미가 맞는지** 확인한다.

- [ ] T01 전체 고유 과정 수
- [ ] T02 전체 개설 회차 수
- [ ] T03 기간별 개설 추이
- [ ] T04 지역별 과정/회차 현황
- [ ] T05 NCS 세분류별 시장 규모
- [ ] T06 NCS 대분류별 시장 규모
- [ ] T07 기관별 개설 현황
- [ ] T08 평균 만족도 + Coverage
- [ ] T09 6개월 취업률 + Coverage
- [ ] T10 정원 대비 신청 인원

### 최소 필수 기대

```text
T01 != T02
```

그리고 NCS 쿼리에서 미매칭 데이터가 조용히 사라지지 않아야 한다.

---

## 14. Reference Reconciliation

반드시 세 단계 비교:

```text
Raw CSV
   ↓
Cleaned DataFrame
   ↓
PostgreSQL
```

확인 항목:

| Metric | Raw | Cleaned | PostgreSQL | Result |
|---|---:|---:|---:|---|
| Row count | 628,384 | 619,537 | 619,537 | [ ] |
| Exact duplicate | 8,847 | 제거 | - | [ ] |
| course_count | 확인 | 139,138 | 139,138 | [ ] |
| course_run_count | - | 619,537 | 619,537 | [ ] |
| PK NULL | 확인 | 0 | 0 | [ ] |
| PK duplicate | 확인 | 0 | 0 | [ ] |
| NCS non-null | 확인 | 619,029 | 619,029 | [ ] |
| NCS matched | - | 596,177 | 596,177 | [ ] |
| NCS unmatched | - | 22,852 | 22,852 | [ ] |

하나라도 다르면 SQL을 먼저 고치지 말고
**어느 처리 단계에서 값이 달라졌는지 추적한다.**

---

## 15. ETL Re-run Check

- [ ] 동일 입력으로 재실행 가능하다.
- [ ] 재실행 후 최종 행 수가 동일하다.
- [ ] 중복 적재가 발생하지 않는다.
- [ ] 동일한 PK/Metric 결과가 나온다.
- [ ] 실패 시 원인을 로그에서 확인할 수 있다.

파일럿에서는 복잡한 orchestration이나 별도 로그 DB는 필요 없다.

---

## 16. Minimum File Check

Phase 1 최소 구현 파일:

```text
database/
  connection.py
  schema.sql
  queries.py

pipeline/
  load_ncs_codes.py
  load_training_courses.py

tests/
  test_phase1_validation.py
```

검토:

- [ ] 위 파일이 존재한다.
- [ ] 불필요한 구조가 추가되지 않았다.
- [ ] 코드가 과도하게 추상화되지 않았다.

---

## 17. Gate 1 Final Decision

### PASS 조건

아래를 모두 만족:

- [ ] PostgreSQL 정상 적재
- [ ] 619,537행 일치
- [ ] PK NULL/중복 0
- [ ] NCS 1,083건 적재
- [ ] NCS 매칭 공식 수치 재현
- [ ] T01~T10 실행 및 의미 검증
- [ ] Raw/Cleaned/PostgreSQL 핵심 수치 일치
- [ ] 재실행 가능
- [ ] LLM 없이 핵심 시장지표 계산 가능

### 최종 판정

```text
[ ] PASS
[ ] FIX REQUIRED
```

### FIX REQUIRED일 경우

다음 형식만 기록한다.

```text
실패 항목:
원인:
영향:
수정 대상 파일:
재검증 방법:
```

---

## 18. Gate 1 완료 후

Gate 1 PASS 전에는 Phase 2 구현으로 넘어가지 않는다.

Gate 1 PASS 후 다음 단계:

```text
Phase 2
Document Ingestion & Retrieval Foundation
```

이때도 새로운 기능을 먼저 추가하지 않고,
보유 비정형 문서 Inventory 및 Parser/Chunking 기준부터 확인한다.
