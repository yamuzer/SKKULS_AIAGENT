CREATE SCHEMA IF NOT EXISTS training;

SELECT
	current_user as login_user,
	current_database() as database_name;

BEGIN;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
COMMIT;

COMMENT ON SCHEMA raw IS
'외부 시스템에서 수집한 원본 데이터를 가능한 그대로 보관하는 스키마';

COMMENT ON SCHEMA staging IS
'원본 데이터와 정제, 표준화, 코드 매핑, 오류 분리를 수행하는 스키마';

COMMENT ON SCHEMA core IS
'고객지원 업무에 사용하는 최종 정규화 데이터 모델 스키마';

SELECT
	n.nspname as schema_name,
	pg_get_userbyid(n.nspowner) as schema_owner,
	obj_description(n.oid, 'pg_namespace') as description
FROM pg_namespace AS n
WHERE n.nspname IN ('raw', 'staging', 'core')
ORDER BY n.nspname;


CREATE TABLE raw.inquiry_raw (
	inquiry_id BIGINT NOT NULL,
	customer_id BIGINT NOT NULL,
	country_name VARCHAR(50),
	language_name VARCHAR(50),
	channel_name VARCHAR(30),
	inquiry_text TEXT,
	received_at TIMESTAMPTZ NOT NULL,
	status_name VARCHAR(20),
	CONSTRAINT pk_inquiry_raw PRIMARY KEY (inquiry_id)
);

--DROP TABLE raw.inquiry_raw;

-- COMMENT ON TABLE raw.inquiry_raw IS '';

-- COMMENT ON COLUMN raw.inquiry_raw.inquiry_id IS '';

BEGIN;
INSERT INTO raw.inquiry_raw (
    inquiry_id,
    customer_id,
    country_name,
    language_name,
    channel_name,
    inquiry_text,
    received_at,
    status_name
)
VALUES
(
    10001,
    5001,
    'South Korea',
    'Korean',
    'email',
    '제품 설치 후 로그인이 되지 않습니다.',
    '2026-01-15 10:30:00+09',
    'open'
),
(
    10002,
    5002,
    'Korea',
    '한국어',
    'Web',
    '결제는 완료되었지만 주문 내역이 보이지 않습니다.',
    '2026-01-15 11:10:00+09',
    'pending'
),
(
    10003,
    5003,
    'Japan',
    'Japanese',
    'chat',
    'アカウントのパスワードを変更できません。',
    '2026-01-15 13:20:00+09',
    'open'
),
(
    10004,
    5004,
    'United States',
    'English',
    'Email',
    'The product was delivered with a damaged screen.',
    '2026-01-15 09:15:00-05',
    'in_progress'
),
(
    10005,
    5005,
    'USA',
    'English',
    'web',
    'I would like to cancel my subscription.',
    '2026-01-16 14:40:00-05',
    'resolved'
),
(
    10006,
    5006,
    'Germany',
    'German',
    'email',
    'Die Rechnung enthält einen falschen Betrag.',
    '2026-01-16 16:10:00+01',
    'pending'
),
(
    10007,
    5007,
    'France',
    'French',
    'chat',
    'Je ne peux pas suivre la livraison.',
    '2026-01-17 09:30:00+01',
    'open'
),
(
    10008,
    5008,
    'Singapore',
    'English',
    'mobile_app',
    'The application closes immediately after login.',
    '2026-01-17 18:25:00+08',
    'in_progress'
),
(
    10009,
    5001,
    'South Korea',
    'Korean',
    'phone',
    '기존 문의에 대한 처리 결과를 확인하고 싶습니다.',
    '2026-01-18 10:05:00+09',
    'closed'
),
(
    10010,
    5009,
    'Korea',
    'Korean',
    'email',
    NULL,
    '2026-01-18 11:45:00+09',
    'open'
),
(
    10011,
    5010,
    'Japan',
    'Japanese',
    'web',
    '',
    '2026-01-18 15:20:00+09',
    'pending'
),
(
    10012,
    5011,
    'United States',
    'English',
    NULL,
    'I cannot download the invoice PDF.',
    '2026-01-19 08:50:00-08',
    'open'
),
(
    10013,
    5012,
    'Germany',
    'English',
    'chat',
    'Please change the delivery address.',
    '2026-01-19 13:15:00+01',
    'resolved'
),
(
    10014,
    5013,
    'South Korea',
    'Korean',
    'mobile_app',
    '앱에서 알림 설정을 변경할 수 없습니다.',
    '2026-01-20 09:40:00+09',
    'in_progress'
),
(
    10015,
    5014,
    NULL,
    'English',
    'email',
    'The country information was not included in the source data.',
    '2026-01-20 17:30:00+00',
    'pending'
)

-- 같은 inquiry_id가 이미 있으면 오류 없이 건너뜀
ON CONFLICT (inquiry_id) DO NOTHING

RETURNING
    inquiry_id,
    customer_id,
    country_name,
    received_at;
COMMIT;

SELECT
	COUNT (*) AS inserted_row_count
FROM raw.inquiry_raw
WHERE inquiry_id BETWEEN 10001 AND 10015;

SELECT inquiry_id, country_name, channel_name, inquiry_text
FROM raw.inquiry_raw
WHERE inquiry_id BETWEEN 10001 AND 10015;

SELECT
	inquiry_id, contry_name, inquiry_text
FROM raw.inquiry_raw;

BEGIN;
INSERT INTO raw.inquiry_raw(
	inquiry_id, customer_id, received_at, status_name
)
VALUES
	(1, 100, '2026-01-22 10:10:00+09' ,'OPEN'),
	(2, 101, '2026-01-22 10:30:00-01' ,'CLOSED')
ON CONFLICT (inquiry_id) DO NOTHING;
COMMIT;
	()


SELECT 
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간"
FROM raw.inquiry_raw
--WHERE status_name = 'open';
-- WHERE inquiry_id > 10010;
WHERE status_name <> 'closed';


SELECT
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간",
	status_name
FROM raw.inquiry_raw
WHERE status_name IN ('open', 'pending');


SELECT
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간",
	status_name
FROM raw.inquiry_raw
WHERE (
		country_name ='South Korea'
		OR country_name = 'Japan'
      )
  AND status_name = 'open';


SELECT
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간",
	status_name
FROM raw.inquiry_raw
WHERE country_name in ('South Korea','Japan')
  AND status_name = 'open';


SELECT
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간",
	status_name,
	inquiry_text
FROM raw.inquiry_raw
WHERE inquiry_text IS NULL;


SELECT
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간",
	status_name,
	inquiry_text
FROM raw.inquiry_raw
WHERE inquiry_text = NULL;


SELECT
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간",
	status_name,
	inquiry_text
FROM raw.inquiry_raw
WHERE inquiry_text IS NULL
   OR inquiry_text = '';


SELECT
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간",
	status_name,
	inquiry_text
FROM raw.inquiry_raw
WHERE inquiry_text IS NULL
   OR TRIM(inquiry_text) = '';



SELECT
	inquiry_id,
	channel_name,
	COALESCE(channel_name, 'unknown') as display_channel
FROM raw.inquiry_raw;


SELECT
	inquiry_id,
	country_name,
	received_at
FROM raw.inquiry_raw
WHERE received_at BETWEEN '2026-01-15 00:00:00+09' AND '2026-01-17 23:59:59+09'
ORDER BY received_at;

SELECT
	inquiry_id,
	country_name,
	received_at
FROM raw.inquiry_raw
WHERE received_at >= '2026-01-15 00:00:00+09' 
  AND received_at <'2026-01-18 00:00:00+09'
ORDER BY received_at;


SELECT
	inquiry_id,
	inquiry_text
FROM raw.inquiry_raw
WHERE inquiry_text LIKE '%rech%';

select * from raw.inquiry_raw;

SELECT 
	inquiry_id,
	country_name,
	received_at
FROM raw.inquiry_raw
ORDER BY received_at DESC;

SELECT 
	inquiry_id,
	country_name,
	received_at
FROM raw.inquiry_raw
ORDER BY 
	country_name ASC,
	received_at DESC;

SELECT 
	inquiry_id,
	country_name,
	received_at
FROM raw.inquiry_raw
ORDER BY 
	country_name ASC,
	received_at DESC
LIMIT 5;


SELECT 
	inquiry_id,
	country_name,
	received_at
FROM raw.inquiry_raw
ORDER BY 
	country_name ASC,
	received_at DESC
LIMIT 5 OFFSET 5;


SELECT DISTINCT
	country_name
FROM raw.inquiry_raw
ORDER BY country_name;


SELECT DISTINCT
	country_name,
	language_name
FROM raw.inquiry_raw
ORDER BY country_name,
		 language_name;


-- 1. 한국에서 접수된 최신 문의 10건
select *
from raw.inquiry_raw
where country_name in ('Korea', 'South Korea')
order by received_at desc
limit 10;

-- 2. 본문이 비어 있는 문의

select
	inquiry_id,
	customer_id,
	status_name,
	inquiry_text
from raw.inquiry_raw 
where inquiry_text is null
	or inquiry_text = '';


-- 3. open 또는 pending 상태 문의

select
	inquiry_id,
	customer_id,
	status_name,
	inquiry_text,
	received_at
from raw.inquiry_raw 
where status_name in ('open', 'pending');


-- 4. 2026년 1월 데이터 중 최신 5건

select
	inquiry_id,
	customer_id,
	status_name,
	inquiry_text,
	received_at
from raw.inquiry_raw 
where received_at >= '2026-01-01 00:00:00+09'
  and received_at <  '2026-02-01 00:00:00+09'
order by received_at desc
limit 5;


-- 5. 국가와 언어의 유일한 조합

select distinct
	country_name,
	language_name
from raw.inquiry_raw
order by
	country_name,
	language_name;


BEGIN;

UPDATE raw.inquiry_raw
SET status_name = 'closed'
WHERE inquiry_id = 10001
RETURNING
	inquiry_id,
	status_name;

ROLLBACK;

SELECT
	inquiry_id,
	status_name
FROM raw.inquiry_raw;



BEGIN;

UPDATE raw.inquiry_raw
SET
	channel_name = NULL,
	status_name = NULL
WHERE inquiry_id = 10012
RETURNING
	inquiry_id,
	channel_name,
	status_name;

COMMIT;

SELECT
	inquiry_id,
	channel_name,
	status_name
FROM raw.inquiry_raw;


BEGIN;

UPDATE raw.inquiry_raw
SET status_name = 'pending'
WHERE status_name = 'open'
  AND (
		inquiry_text IS NULL
		OR TRIM(inquiry_text) = ''
  )
RETURNING
	inquiry_id,
	inquiry_text,
	status_name;

ROLLBACK;

SELECT
	inquiry_id,
	inquiry_text,
	status_name
FROM raw.inquiry_raw;

BEGIN;

UPDATE raw.inquiry_raw
SET inquiry_text = '[확인 필요]' || inquiry_text
WHERE inquiry_id = 10001
RETURNING
	inquiry_id,
	inquiry_text;

ROLLBACK;


	
	
SELECT
	COUNT(*) AS total_inquiry_count
FROM raw.inquiry_raw;


SELECT
	COUNT(*) AS total_inquiry_count,
	COUNT(inquiry_text) AS row_with_inquiry_text
FROM raw.inquiry_raw;


SELECT
	COUNT(*) AS total_rows,
	COUNT(*) FILTER(
		WHERE inquiry_text IS NULL
	)AS null_text_count,
	COUNT(*) FILTER(
		WHERE inquiry_text = ''
	)AS empty_text_count
FROM raw.inquiry_raw;


SELECT
	status_name,
	COUNT(*) AS inquiry_count
FROM raw.inquiry_raw
GROUP BY status_name
ORDER BY inquiry_count DESC;


SELECT
	status_name,
	country_name,
	COUNT(*) AS inquiry_count
FROM raw.inquiry_raw
GROUP BY
	status_name,
	country_name;

-- 국가별 문의 수와 고객 수

SELECT
	country_name,
	COUNT(*) AS inquiry_count,
	COUNT(DISTINCT customer_id) AS unique_customer_count
FROM raw.inquiry_raw
GROUP BY country_name
ORDER BY inquiry_count DESC, country_name ASC;



-- quiz	
-- ---------------------------------------------------------
-- 0. 접속 정보와 테이블 데이터 건수 확인
-- ---------------------------------------------------------

SELECT
    current_user AS login_user,
    current_database() AS database_name,
    (
        SELECT COUNT(*)
        FROM raw.inquiry_raw
    ) AS total_row_count;


-- ---------------------------------------------------------
-- 문제 1. 전체 문의 목록 조회
-- 다음 열을 한글 별칭으로 출력하세요.
--
-- 문의번호, 고객번호, 국가, 언어, 접수채널, 처리상태, 접수시간
--
-- 정렬 조건:
-- 접수시간이 최신인 문의부터 출력합니다.
-- ---------------------------------------------------------

select * from raw.inquiry_raw;

SELECT
	inquiry_id as "문의번호",
	customer_id as "고객번호",
	country_name as "국가",
	channel_name as "접수채널",
	received_at as "접수시간",
	status_name as "처리상태",
	language_name as "언어"
FROM raw.inquiry_raw
ORDER BY received_at DESC;



-- ---------------------------------------------------------
-- 문제 2. 우선 처리 대상 문의 조회
-- 다음 조건을 모두 만족하는 문의를 조회하세요.
--
-- 1. 국가는 Korea, South Korea, Japan 중 하나
-- 2. 처리상태는 open 또는 pending
--
-- 출력 항목:
-- inquiry_id, country_name, language_name,
-- channel_name, status_name, received_at
--
-- 정렬 조건:
-- 처리상태 오름차순, 접수시간 내림차순
-- ---------------------------------------------------------


SELECT inquiry_id, country_name, language_name, channel_name, status_name, received_at
FROM raw.inquiry_raw
where 
	country_name in ('Korea', 'South Korea', 'Japan') 
	and
	(status_name = 'open' or 
	status_name ='pending')
order by status_name ASC, received_at DESC;


-- ---------------------------------------------------------
-- 문제 3. 데이터 품질 점검 대상 조회
-- 문의 본문이 다음 중 하나인 행을 조회하세요.
--
-- 1. NULL
-- 2. 공백을 제거한 결과가 빈 문자열
--
-- channel_name이 NULL이면 'unknown'으로 표시하세요.
--
-- 출력 항목:
-- inquiry_id, customer_id, display_channel,
-- inquiry_text, status_name
-- ---------------------------------------------------------

SELECT 
	inquiry_id, 
	customer_id, 
	inquiry_text, 
	status_name, 
	COALESCE(channel_name, 'unknown') as display_channel
FROM raw.inquiry_raw
WHERE inquiry_text IS NULL
OR TRIM(inquiry_text) = '';



-- ---------------------------------------------------------
-- 문제 4. 특정 기간의 최신 문의 조회
-- 한국 시간 기준으로 다음 기간에 접수된 문의를 조회하세요.
--
-- 시작: 2026-01-15 00:00:00+09 이상
-- 종료: 2026-01-19 00:00:00+09 미만
--
-- 출력 항목:
-- inquiry_id, country_name, received_at, inquiry_text
--
-- 최신순으로 정렬한 뒤 상위 5건만 출력하세요.
-- ---------------------------------------------------------
SELECT
	inquiry_id, 
	country_name, 
	received_at, 
	inquiry_text
FROM raw.inquiry_raw
WHERE (received_at >= '2026-01-15 00:00:00+09' 
	AND received_at < '2026-01-19 00:00:00+09')
ORDER BY received_at DESC
LIMIT 5;


-- ---------------------------------------------------------
-- 문제 5. 국가와 언어 조합 확인
-- country_name과 language_name의 유일한 조합을 조회하세요.
--
-- 정렬 조건:
-- country_name 오름차순, language_name 오름차순
-- ---------------------------------------------------------
SELECT DISTINCT country_name, language_name
FROM raw.inquiry_raw
ORDER BY 
country_name ASC, 
language_name ASC;


-- ---------------------------------------------------------
-- 문제 6. 트랜잭션을 이용한 안전한 수정 연습
-- inquiry_id가 10010인 문의에 대해 다음 작업을 수행하세요.
--
-- 1. 트랜잭션을 시작합니다.
-- 2. 문의 본문이 NULL 또는 빈 문자열일 때만
--    inquiry_text를 '[본문 확인 필요]'로 변경합니다.
-- 3. status_name을 'pending'으로 변경합니다.
-- 4. 변경된 inquiry_id, inquiry_text, status_name을
--    RETURNING으로 확인합니다.
-- 5. ROLLBACK하여 변경을 취소합니다.
-- 6. 마지막 SELECT로 원래 값이 유지되는지 확인합니다.
--
-- 주의: COMMIT하지 않습니다.
-- ---------------------------------------------------------

BEGIN;

UPDATE raw.inquiry_raw
SET
    inquiry_text = '[본문 확인 필요]',
    status_name = 'pending'
WHERE inquiry_id = 10010
  AND (
        inquiry_text IS NULL
        OR TRIM(inquiry_text) = ''
      )
RETURNING
    inquiry_id,
    inquiry_text,
    status_name;

ROLLBACK;

SELECT
    inquiry_id,
    inquiry_text,
    status_name
FROM raw.inquiry_raw
WHERE inquiry_id = 10010;



-- ---------------------------------------------------------
-- 문제 7. 처리상태별 문의 건수
-- 처리상태별 문의 건수를 계산하세요.
--
-- 출력 항목:
-- status_name, inquiry_count
--
-- status_name이 NULL이면 'unknown'으로 묶어 표시하세요.
-- 문의 건수가 많은 순서로 정렬하세요.
-- ---------------------------------------------------------

SELECT
    COALESCE(status_name, 'unknown') AS status_name,
    COUNT(*) AS inquiry_count
FROM raw.inquiry_raw
GROUP BY COALESCE(status_name, 'unknown')
ORDER BY
    inquiry_count DESC,
    status_name ASC;

-- ---------------------------------------------------------
-- 문제 8. 국가별 고객지원 현황
-- 국가별로 다음 값을 계산하세요.
--
-- 1. 전체 문의 수: inquiry_count
-- 2. 고유 고객 수: unique_customer_count
-- 3. open 또는 pending 상태 문의 수: active_inquiry_count
--
-- country_name이 NULL이면 'unknown'으로 표시하세요.
--
-- 정렬 조건:
-- 전체 문의 수 내림차순, 국가명 오름차순
-- ---------------------------------------------------------

SELECT
    COALESCE(country_name, 'unknown') AS country_name,
    COUNT(*) AS inquiry_count,
    COUNT(DISTINCT customer_id) AS unique_customer_count,
    COUNT(*) FILTER (
        WHERE status_name IN ('open', 'pending')
    ) AS active_inquiry_count
FROM raw.inquiry_raw
GROUP BY COALESCE(country_name, 'unknown')
ORDER BY
    inquiry_count DESC,
    country_name ASC;



-- ---------------------------------------------------------
-- 문제 9. 전체 데이터 품질 요약
-- 하나의 행으로 다음 값을 출력하세요.
--
-- total_count              : 전체 문의 수
-- null_text_count          : inquiry_text가 NULL인 수
-- blank_text_count         : inquiry_text가 NULL은 아니지만
--                            TRIM 결과가 빈 문자열인 수
-- missing_channel_count    : channel_name이 NULL인 수
-- missing_country_count    : country_name이 NULL인 수
-- ---------------------------------------------------------
SELECT
    COUNT(*) AS total_count,
    COUNT(*) FILTER (
        WHERE inquiry_text IS NULL
    ) AS null_text_count,
    COUNT(*) FILTER (
        WHERE inquiry_text IS NOT NULL
          AND TRIM(inquiry_text) = ''
    ) AS blank_text_count,
    COUNT(*) FILTER (
        WHERE channel_name IS NULL
    ) AS missing_channel_count,
    COUNT(*) FILTER (
        WHERE country_name IS NULL
    ) AS missing_country_count
FROM raw.inquiry_raw;


--- having
SELECT
	status_name,
	COUNT(*) as inquiry_count
FROM raw.inquiry_raw
GROUP BY status_name
HAVING COUNT(*) >= 3;

-- 문의가 두 건 이상인 국가명
SELECT 
	country_name,
	COUNT(*) AS inquiry_count,
	COUNT(DISTINCT customer_id) as unique_customer_count
FROM raw.inquiry_raw
WHERE country_name IS NOT NULL
GROUP BY country_name
HAVING COUNT(*) >= 2
ORDER BY inquiry_count DESC, country_name;

-- 행을 배열로 집계
SELECT 
	status_name,
	COUNT(*) AS inquiry_count,
	ARRAY_AGG(inquiry_id ORDER BY inquiry_id) AS inquiry_id
FROM raw.inquiry_raw
GROUP BY status_name;


-- DATE / TIMESTAMP 함수
SHOW TIME ZONE;
--SET TIME ZONE 'ASIA/SEOUL';

-- DATE_TRUNC : 자르기
-- 지정한 단위 아래를 0 으로 채웁니다. 'day' 는 시각을 00:00:00 으로 맞춥니다.
SELECT
	inquiry_id,
	received_at,
	DATE_TRUNC('day', received_at)::date AS d_day,
	CAST(DATE_TRUNC('hour', received_at) AS date) AS d_hour,
	DATE_TRUNC('month', received_at)::date AS d_month
FROM raw.inquiry_raw
ORDER BY inquiry_id
LIMIT 10;

-- EXTRACT: 부분 추출
-- 년/월/일/시/분/초/요일 등 원하는 부분만 정수로 추출합니다.
SELECT
	EXTRACT(year FROM received_at) AS yr,
	EXTRACT(month FROM received_at) AS mo,
	EXTRACT(day FROM received_at) AS day,
	EXTRACT(dow FROM received_at) AS dow, -- 요일, 0=일, ISODOW는 7=일
	EXTRACT(epoch FROM received_at) AS ts
FROM raw.inquiry_raw
LIMIT 5;

-- 날짜별 문의 건수 고유 고객 수
SELECT
	DATE_TRUNC('day', received_at)::date AS inquiry_date,
	COUNT(*) AS inquiry_count,
	COUNT(DISTINCT customer_id) AS unique_customer_count
FROM raw.inquiry_raw
GROUP BY
	DATE_TRUNC('day', received_at)::date
ORDER BY inquiry_date;
	


-- 요일별 문의량 분석
SELECT
	EXTRACT(ISODOW FROM received_at)::integer AS day_of_week,
	CASE EXTRACT(ISODOW FROM received_at)::integer
		WHEN 1 THEN '월요일'
		WHEN 2 THEN '화요일'
		WHEN 3 THEN '수요일'
		WHEN 4 THEN '목요일'
		WHEN 5 THEN '금요일'
		WHEN 6 THEN '토요일'
		WHEN 7 THEN '일요일'
	END AS day_name,
	COUNT(*) AS inquiry_count
FROM raw.inquiry_raw
GROUP BY
	EXTRACT(ISODOW FROM received_at)::integer
ORDER BY day_of_week;

-- 컴퓨터(DB Engine)가 똑같은 EXTRACT 연산을 여러 번 하는 것처럼 보여서 비효율적으로 느껴지지만, 사실 DB 내부의 최적화 도구(Optimizer)가 아주 똑똑해서 한 번 계산한 결과 값을 메모리에 올려두고 재사용합니다. 즉, 겉보기에는 중복 코드가 있어 지저분해 보일지라도 실제 성능(속도)에는 아무런 악영향을 주지 않습니다.


-- 연도와 월을 별도 칼럼으로 출력
SELECT
	EXTRACT(YEAR FROM received_at)::integer AS inquiry_year,
	EXTRACT(MONTH FROM received_at)::integer AS inquiry_month,
	COUNT(*) AS inquiry_count
FROM raw.inquiry_raw
GROUP BY
	EXTRACT(YEAR FROM received_at)::integer,
	EXTRACT(MONTH FROM received_at)::integer
ORDER BY inquiry_year, inquiry_month;

-- 데이터 탐색
SELECT 
	COUNT(*) AS total_rows,
	COUNT(DISTINCT inquiry_id) AS unique_inquiry_count,
	COUNT(DISTINCT customer_id) AS unique_customer_count,
	COUNT(*) FILTER(
		WHERE country_name IS NULL
		OR BTRIM(country_name) = ''
	)  AS invalid_country_count,
	COUNT(*) FILTER(
		WHERE language_name IS NULL
		OR BTRIM(language_name) = ''
	)  AS invalid_language_count
FROM raw.inquiry_raw



