# SmartHRD Training Courses — DATA DICTIONARY

- **Version:** v1.1
- **Status:** Phase 1 working specification
- **Source:** 고용24 국민내일배움카드 훈련과정 API - 목록
- **Target Table:** PostgreSQL `training_courses`
- **Source CSV:** `2101-2604_국민내일배움카드_훈련과정_목록_정제본.csv`
- **CSV Columns:** 23개 (`index` 포함, 업무 컬럼 22개)
- **Region Master:** MVP 제외

## 1. 목적

이 문서는 고용24 국민내일배움카드 훈련과정 API의 원본 필드와
SmartHRD PostgreSQL `training_courses` 스키마 사이의 의미, 타입,
NULL 정책, 분석 용도를 고정한다.

### 원칙

1. API의 `string`은 전송 형식이다. PostgreSQL에서는 비즈니스 의미에 맞는 타입으로 변환한다.
2. ID/Code는 산술 연산 대상이 아니므로 문자열을 우선한다.
3. NULL을 임의로 `0`, 빈 문자열 또는 평균값으로 치환하지 않는다.
4. 공식 API 명세에서 확인된 의미만 사용한다.
5. `ncsCd`는 CSV에서 float처럼 읽혀 선행 0이 탈락될 수 있으므로 정규화 규칙을 적용한다.
6. **ncsCd 공식 정규화 규칙 확정:** NULL이면 NULL 유지, 문자열 변환, trailing `.0` 제거 후 8자리보다 짧은 유효 코드에 대해 `zfill(8)`을 적용하여 `VARCHAR(8)`로 저장한다. 단, 비정상 형식 임의 수정 금지, 실패 시 로그 기록, Master 미매칭 값을 임의 코드로 변경하지 않는다.
7. `index`는 CSV 생성 과정의 보조 컬럼으로 PostgreSQL 적재 전에 제거한다.
8. 실제 `NOT NULL` 제약은 ETL Data Quality Validation 결과를 확인한 뒤 최종 DDL에서 확정한다.

## 2. 컬럼 사전

| 원본 컬럼 | DB 컬럼 | 공식 의미 | PostgreSQL Type | NULL | Key/Code | Agent 활용 | 주의사항 |
|---|---|---|---|---|---|---|---|
| `index` | - | CSV 생성 과정의 인덱스 | - | - | - | 제외 | PostgreSQL 적재 전 제거. 업무 데이터가 아님 |
| `trprId` | `trpr_id` | 훈련과정ID | `VARCHAR` | NOT NULL | **PK / ID** | 과정 식별, `course_count` 계산 | `trpr_degr`와 복합 PK. 숫자형 변환 금지 |
| `trprDegr` | `trpr_degr` | 훈련과정 순차 | `INTEGER` | NOT NULL | **PK 구성요소** | 개설 회차 식별, `course_run_count` 계산 | API는 string 전달. 값은 회차이므로 정수 변환 |
| `title` | `title` | 제목 | `TEXT` | NOT NULL 후보 | - | 과정명 검색/표시 | 과정명 텍스트 |
| `subTitle` | `sub_title` | 부 제목 | `TEXT` | NOT NULL 후보 | - | 부제목 표시 (기관명 label 후보) | 공식 정의는 '부 제목' 유지. 기관 식별 기준은 `trainst_cst_id`이며, 기관별 집계는 반드시 `GROUP BY trainst_cst_id`만 사용 |
| `trainstCstId` | `trainst_cst_id` | 훈련기관ID | `VARCHAR` | NOT NULL 후보 | **ID** | 기관별 과정 수, 기관 기준 필터, 기관 집계 Key | 훈련기관 유일 식별자이므로 기관별 집계 시 반드시 단독 GROUP BY 키로 사용 |
| `traStartDate` | `tra_start_date` | 훈련시작일자 | `DATE` | NOT NULL 후보 | - | 기간 필터, 시계열 분석 | 날짜 변환 실패 건수 검증 |
| `traEndDate` | `tra_end_date` | 훈련종료일자 | `DATE` | NOT NULL 후보 | - | 기간 필터, 종료 과정 판별 | `tra_end_date >= tra_start_date` 검증 |
| `address` | `address` | 주소 | `TEXT` | NOT NULL 후보 | - | 지역 텍스트 필터/집계 | MVP에서는 Region Master 없이 원문 보존 |
| `ncsCd` | `ncs_cd` | NCS 코드 | `VARCHAR(8)` | NULL 허용 | **Code** | NCS 분류 조인, 직종 분석 | CSV에서 float 파싱으로 선행 0 탈락 확인. trailing `.0` 제거 및 8자리 미만 유효 코드에 `zfill(8)` 정규화 적용. Soft FK 유지 |
| `trainTarget` | `train_target` | 훈련대상 | `TEXT` | NOT NULL 후보 | - | 훈련대상별 필터/집계 | 원문 범주 우선 보존 |
| `courseMan` | `course_man` | 수강비 | `BIGINT` | NOT NULL 후보 | - | 비용 분석 | 금액 필드. 소수점 존재 여부 ETL에서 검증 |
| `realMan` | `real_man` | 실제 훈련비 | `BIGINT` | NOT NULL 후보 | - | 실제 훈련비 분석 | `course_man`과 별개 지표 |
| `regCourseMan` | `reg_course_man` | 수강신청 인원 | `INTEGER` | NOT NULL 후보 | - | 신청 인원, 충원 관련 분석 | 인원 필드. 음수/비정상값 검증 |
| `yardMan` | `yard_man` | 정원 | `INTEGER` | NOT NULL 후보 | - | 정원, 충원율 분석 | `yard_man = 0` 처리 규칙 필요 |
| `stdgScor` | `stdg_scor` | 만족도 점수 | `NUMERIC` | NULL 허용 | - | 만족도 비교/평균 | NULL과 0점 구분. 값 범위 검증 |
| `eiEmplCnt3` | `ei_empl_cnt_3` | 고용보험 3개월 취업인원 수 | `INTEGER` | NULL 허용 | - | 취업성과 분석 | NULL을 0명으로 해석하지 않음 |
| `eiEmplRate3` | `ei_empl_rate_3` | 고용보험 3개월 취업률 | `NUMERIC` | NULL 허용 | - | 3개월 취업률 분석 | 평균 산출 시 유효 건수/커버리지 병기 |
| `eiEmplRate6` | `ei_empl_rate_6` | 고용보험 6개월 취업률 | `NUMERIC` | NULL 허용 | - | 6개월 취업률 분석 | 평균 산출 시 유효 건수/커버리지 병기 |
| `telNo` | `tel_no` | 전화번호 | `VARCHAR` | NULL 허용 | - | 기관 연락처 표시 | 숫자형 저장 금지. 하이픈 보존 |
| `titleLink` | `title_link` | 제목 링크 | `TEXT` | NULL 허용 | - | 과정 상세 페이지 이동 | URL 원문 보존 |
| `subTitleLink` | `sub_title_link` | 부 제목 링크 | `TEXT` | NULL 허용 | - | 기관/부제 관련 상세 이동 | URL 원문 보존 |
| `wkendSe` | `wkend_se` | 주말/주중 구분 | `VARCHAR` | NULL 허용 | **Code** | 주중/주말 과정 필터 | 공식 명세: `0=해당없음`, `1=주말`, `2=주말·주중 혼합`, `3=주중`. 원본 데이터의 `9`(136,789건)는 공식 명세 미확인 코드로 '9' 문자열 보존 (임의로 '기타/미지정' 확정 금지) |

## 3. CSV ↔ Data Dictionary 대조 결과

현재 정제본 CSV 헤더:

```text
index,
eiEmplRate6,
eiEmplCnt3,
eiEmplRate3,
title,
realMan,
telNo,
stdgScor,
traStartDate,
ncsCd,
regCourseMan,
trprDegr,
address,
traEndDate,
subTitle,
trprId,
yardMan,
courseMan,
trainTarget,
trainstCstId,
subTitleLink,
titleLink,
wkendSe
```

결론:

- 총 23개 컬럼
- `index` 1개는 적재 제외
- PostgreSQL `training_courses` 업무 컬럼은 **22개**
- Data Dictionary와 현재 CSV 헤더는 누락 없이 1:1 대응한다.

## 4. 공식 API 명세에서 확인했지만 현재 MVP CSV에 포함하지 않는 필드

API 목록 명세에는 현재 정제본 CSV 외에도 다음과 같은 출력 필드가 존재한다.

| API 필드 | 공식 의미 | MVP 처리 |
|---|---|---|
| `CERTIFICATE` | 자격증 | 제외 |
| `CONTENTS` | 컨텐츠 | 제외 |
| `GRADE` | 등급 | 제외 |
| `INST_CD` | 훈련기관 코드 | 제외 |
| `TITLE_ICON` | 제목 아이콘 | 제외 |
| `TRAIN_TARGET_CD` | 훈련구분 | 제외 |
| `TRNG_AREA_CD` | 지역코드(중분류) | Region Master 설계 시 재검토 |
| `EI_EMPL_CNT3_G10` | 고용보험 3개월 취업인원 관련 필드 | 필요성 확인 후 재검토 |

MVP 원칙상 현재 CSV에 없는 필드를 추가 수집하기 위해 ETL 범위를 확장하지 않는다.

## 5. Primary Key

```sql
PRIMARY KEY (trpr_id, trpr_degr)
```

의미:

- `trpr_id` = 훈련과정
- `trpr_degr` = 해당 훈련과정의 개설 회차
- 두 컬럼의 조합이 하나의 과정 회차를 식별한다.

기존 profiling 결과:

- 원본: 628,384행
- `index` 제외 완전중복: 8,847행
- 중복 제거 후: 619,537행
- `(trprId, trprDegr)` 중복: 0
- 두 필드 NULL: 0

따라서 MVP Fact Table의 복합 PK로 사용한다.

## 6. Semantic Metrics

### 6.1 고유 과정 수

```sql
COUNT(DISTINCT trpr_id)
```

내부 metric name:

```text
course_count
```

### 6.2 개설 회차 수

중복 제거 및 PK 유일성 보장 후:

```sql
COUNT(*)
```

내부 metric name:

```text
course_run_count
```

Agent는 **과정 수**와 **개설 회차 수**를 같은 지표로 취급하지 않는다.

### 6.3 충원 관련 지표

예시:

```sql
reg_course_man::numeric / NULLIF(yard_man, 0)
```

주의:

- `yard_man = 0`이면 0으로 나누지 않는다.
- 신청 인원과 정원은 의미가 다르므로 원본값도 함께 유지한다.

### 6.4 성과지표

`ei_empl_cnt_3`, `ei_empl_rate_3`, `ei_empl_rate_6`, `stdg_scor`는
NULL이 존재할 수 있다.

Agent가 평균/비율을 답변할 때 가능한 경우 다음을 함께 계산한다.

- 유효 데이터 건수
- 전체 대상 건수
- 데이터 커버리지

NULL을 `0%`, `0명`, `0점`으로 해석하지 않는다.

## 7. ETL Type Rules

```text
Raw CSV
  ↓
index 제거
  ↓
업무 컬럼 기준 완전중복 제거
  ↓
문자열 정리
  ↓
ID / Code → string
Date → date
Count → integer
Money → bigint
Rate / Score → numeric
  ↓
Schema / Data Quality Validation
  ↓
PostgreSQL Load
```

### 7.1 NCS 코드

`ncs_cd`는 식별 코드다.

- pandas에서 float로 유지하지 않는다.
- CSV의 `12345678.0` 표현은 정규화 대상이다.
- **공식 정규화 규칙:**
  - `ncsCd`가 NULL이면 NULL 유지
  - 문자열 변환 후 trailing `.0` 제거
  - 8자리보다 짧은 유효 코드에 대해 `zfill(8)` 적용
  - 최종 `VARCHAR(8)`로 저장
  - 비정상 형식 임의 수정 금지, 정규화 실패 시 로그 기록, Master 미매칭 값을 임의 코드로 변경하지 않음
- NCS Master 실측 결과, 8자리 복원 시 96.31% 정상 매칭 확인.

### 7.2 금액

`course_man`, `real_man`은 금액 필드다.

MVP 권장 타입:

```sql
BIGINT
```

ETL에서 다음을 확인한다.

- 소수점 존재 여부
- 음수 존재 여부
- 변환 실패 건수

### 7.3 주말/주중 구분

공식 API 명세에 정의된 코드:

| 코드 | 의미 |
|---|---|
| `0` | 해당없음 |
| `1` | 주말 |
| `2` | 주말·주중 혼합 |
| `3` | 주중 |

실제 데이터의 `9` (136,789건):
- 공식 API 명세에는 정의가 없음.
- DB에는 원본 문자열인 `'9'`로 보존한다.
- 문서, Agent, UI에서 '기타'나 '미지정'으로 공식 의미처럼 확정하지 않고, `unknown / 공식 명세 미확인 코드` 수준으로 처리한다.

## 8. NCS Master 연결 (Soft FK 및 LEFT JOIN)

MVP 관계:

```text
training_courses.ncs_cd
        ↓ (Soft FK, INDEX)
ncs_codes.detail_cd
```

- NCS Master(2022-03)와 훈련과정 데이터 간에 신설/개편으로 인한 미매칭(3.69%)이 존재하므로 **Hard FK를 설정하지 않는다.**
- Soft FK 및 인덱스를 유지하며, 분석 SQL에서는 반드시 **`LEFT JOIN`을 사용하여 미매칭 데이터가 누락되지 않도록 보존**한다.
- Master 미매칭 데이터도 `training_courses`에 정상 적재되며, ETL ERROR로 처리하지 않는다.

## 9. Region 처리

MVP에서는:

```text
training_courses.address
```

를 그대로 사용한다.

`TRNG_AREA_CD`, 시군구 Master, 지역코드 정규화는
사용자가 지역코드 자료를 제공한 뒤 별도 설계한다.

현재 Phase 1을 막지 않는다.

## 10. Phase 1 Validation Checklist

- [x] 실제 CSV 헤더 23개 컬럼을 확인했다.
- [x] `index`가 업무 컬럼이 아님을 확인했다.
- [x] Data Dictionary의 22개 업무 컬럼과 CSV 헤더가 1:1 대응한다.
- [x] `(trpr_id, trpr_degr)`를 복합 PK 후보로 확정했다.
- [ ] ETL에서 `index`가 제거된다.
- [ ] 업무 컬럼 기준 완전중복이 제거된다.
- [ ] `(trpr_id, trpr_degr)`가 NULL 없이 유일함을 재검증한다.
- [ ] 날짜 변환 실패 건수를 계산한다.
- [ ] 금액/인원/점수/취업률 타입 변환 실패 건수를 계산한다.
- [ ] NULL을 임의로 0으로 변환하지 않는다.
- [ ] `ncs_cd`가 문자열로 보존된다.
- [ ] NCS Master 매칭률을 계산한다.
- [ ] `course_count`와 `course_run_count`를 원본과 SQL 결과로 대조한다.
- [ ] ETL 재실행 시 동일한 결과를 만든다.

## 11. 아직 열어둘 항목

현재 구현을 막지 않으며 후속 단계에서 검토한다.

- Region Master / `TRNG_AREA_CD`
- NCS 2022 이후 신설·개편 코드 보완
- API 추가 출력 필드 수집 여부
- NCS 능력단위 이하 상세정보의 VectorDB 활용
- 산업/직종 구인 데이터와 NCS Mapping
