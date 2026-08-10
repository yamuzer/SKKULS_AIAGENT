# 크롤링 포함 고객 문의 전체 품질 파이프라인

## 프로젝트 목적

정적 고객 문의 페이지를 크롤링한 뒤
표준화, 품질 검증, 리포트 생성과 선택적 PostgreSQL 적재까지
하나의 실행 흐름으로 처리합니다.

기존 실습 결과와 구분하기 위해 데이터베이스, 스키마,
테이블 이름을 별도로 구성했습니다.

## PostgreSQL 구조

```text
Database
└─ customer_quality_practice

   Schema
   └─ web_inquiry_quality

      Tables
      ├─ pipeline_run_history
      ├─ web_inquiry_raw
      ├─ web_inquiry_standardized
      ├─ web_inquiry_valid
      ├─ web_inquiry_rejected
      └─ web_inquiry_quality_issue
```

## 전체 처리 흐름

```text
정적 고객 문의 HTML
→ requests 크롤링
→ 원본 HTML·원천 CSV 저장
→ 기준정보 기반 표준화
→ 품질 규칙 검증
→ 정상·오류 분리
→ CSV·JSON·HTML 리포트
→ 선택적 PostgreSQL 적재
```

## 프로젝트 구조

```text
customer_inquiry_full_pipeline_lab/
├─ run_full_pipeline.py
├─ src/
│  ├─ crawler.py
│  ├─ config_loader.py
│  ├─ standardizer.py
│  ├─ quality_checker.py
│  ├─ reporting.py
│  ├─ database.py
│  └─ pipeline.py
├─ config/
│  ├─ .env.example
│  ├─ database_structure.json
│  ├─ quality_rules.json
│  └─ reference/
├─ site/
│  └─ customer_inquiries.html
├─ data/
│  └─ raw/
├─ output/
├─ reports/
├─ sql/
│  ├─ 01_create_database.sql
│  └─ verification_queries.sql
├─ requirements.txt
└─ README.md
```

## 1. 패키지 설치

```bat
python -m pip install -r requirements.txt
```

## 2. 파일 파이프라인 실행

PostgreSQL 없이 크롤링부터 품질 리포트까지 실행합니다.

```bat
python run_full_pipeline.py
```

기본 로컬 HTTP 서버 포트는 `8030`입니다.

다른 포트를 사용하려면:

```bat
python run_full_pipeline.py --port 8130
```

## 3. 기존 원천 CSV 재사용

크롤링을 다시 하지 않고 기존 원천 CSV부터 실행합니다.

```bat
python run_full_pipeline.py --skip-crawl
```

## 4. 실습용 데이터베이스 생성

pgAdmin에서 `postgres` 데이터베이스에 연결한 Query Tool을 열고
다음 파일을 실행합니다.

```text
sql/01_create_database.sql
```

생성 SQL:

```sql
CREATE DATABASE customer_quality_practice
    WITH
    ENCODING = 'UTF8'
    TEMPLATE = template0;
```

실행 후 Databases를 새로고침합니다.

## 5. PostgreSQL 환경설정

Windows 명령 프롬프트:

```bat
copy config\.env.example config\.env
```

PowerShell:

```powershell
Copy-Item config/.env.example config/.env
```

`config/.env`에서 비밀번호를 수정합니다.

```text
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=customer_quality_practice
PGUSER=postgres
PGPASSWORD=실제_PostgreSQL_비밀번호
PGSCHEMA=web_inquiry_quality
SQLALCHEMY_ECHO=false
```

## 6. 크롤링부터 PostgreSQL 적재까지 실행

```bat
python run_full_pipeline.py --load-db
```

기존 원천 CSV를 재사용하면서 DB 적재까지 실행하려면:

```bat
python run_full_pipeline.py --skip-crawl --load-db
```

## 실행 모드

| 명령 | 크롤링 | 품질 처리 | DB 적재 |
|---|---:|---:|---:|
| `python run_full_pipeline.py` | 실행 | 실행 | 생략 |
| `python run_full_pipeline.py --skip-crawl` | 생략 | 실행 | 생략 |
| `python run_full_pipeline.py --load-db` | 실행 | 실행 | 실행 |
| `python run_full_pipeline.py --skip-crawl --load-db` | 생략 | 실행 | 실행 |

## PostgreSQL 테이블 설명

### `pipeline_run_history`

파이프라인 실행별 상태와 적재 건수를 기록합니다.

### `web_inquiry_raw`

크롤링으로 수집한 원천 문자열을 저장합니다.

### `web_inquiry_standardized`

국가, 문의유형, 우선순위, 답변상태, 날짜를 표준화한
결과를 저장합니다.

### `web_inquiry_valid`

모든 품질 규칙을 통과한 정상 데이터를 저장합니다.

### `web_inquiry_rejected`

한 개 이상의 품질 규칙을 위반한 데이터를 저장합니다.

### `web_inquiry_quality_issue`

오류 행에서 발견한 규칙별 상세 문제를 저장합니다.

## 예상 결과

```text
크롤링 원천 데이터: 72건
표준화 데이터: 72건
정상 데이터: 63건
오류 데이터: 9건
품질 이슈: 9건
```

## PostgreSQL 확인

다음 파일을 Query Tool에서 실행합니다.

```text
sql/verification_queries.sql
```

확인할 수 있는 내용:

```text
생성된 테이블 목록
최근 실행 이력
테이블별 적재 건수
규칙별 품질 이슈
오류 고객 문의
오류 행과 이슈 상세 JOIN
```
