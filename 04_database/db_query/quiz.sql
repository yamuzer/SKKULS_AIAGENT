-- ============================================================
-- 실습 1. 해외 고객 문의 운영 분석
-- 먼저 01_문제1_데이터준비.sql을 실행하세요.
-- ============================================================

select * from review_inquiry.inquiry_raw;

-- ------------------------------------------------------------
-- 문제 1
-- 처리상태별 문의 건수를 구합니다.
-- 문의가 30건 이상인 상태만 출력합니다.
-- ------------------------------------------------------------

select 
	status_name,
	count(*) as 문의건수
from review_inquiry.inquiry_raw
group by status_name
having count(inquiry_id) >= 30;





-- ------------------------------------------------------------
-- 문제 2
-- 국가별 문의 건수와 고유 고객 수를 구합니다.
-- 문의가 20건 이상인 국가만 출력합니다.
-- ------------------------------------------------------------
select 
	country_name,
	count(distinct customer_id) as 문의건수
from review_inquiry.inquiry_raw
group by country_name
having count(*) >= 20;


-- ------------------------------------------------------------
-- 문제 3
-- 처리상태별 문의번호를 ARRAY_AGG로 묶습니다.
-- 문의번호는 오름차순으로 정렬합니다.
-- ------------------------------------------------------------

select 
	status_name,
	array_agg(inquiry_id) as 문의번호
from review_inquiry.inquiry_raw
group by status_name;


-- ------------------------------------------------------------
-- 문제 4
-- 날짜별 문의 건수와 고유 고객 수를 구합니다.
-- ------------------------------------------------------------

select 
	DATE_TRUNC('day', received_at)::date AS d_day,
	count(inquiry_id) as 문의건수,
	count(distinct customer_id) as 고객수
from review_inquiry.inquiry_raw
group by DATE_TRUNC('day', received_at)::date;


-- ------------------------------------------------------------
-- 문제 5
-- 요일별 문의 건수를 구합니다.
-- ISODOW와 CASE를 사용합니다.
-- ------------------------------------------------------------

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
FROM  review_inquiry.inquiry_raw
GROUP BY
	EXTRACT(
		ISODOW FROM received_at
	)::integer
ORDER BY day_of_week;


-- ------------------------------------------------------------
-- 문제 6
-- 월별 문의 건수와 고유 고객 수를 구합니다.
-- ------------------------------------------------------------

select 
	DATE_TRUNC('month', received_at)::date AS d_day,
	count(inquiry_id) as 문의건수,
	count(distinct customer_id) as 고객수
from review_inquiry.inquiry_raw
group by DATE_TRUNC('month', received_at)::date;


-- ------------------------------------------------------------
-- 문제 7
-- 국가와 처리상태별 문의 건수를 구합니다.
-- 문의 건수가 5건 이상인 조합만 출력합니다.
-- ------------------------------------------------------------
select 
	country_name,
	status_name,
	count(*) as 문의건수
from review_inquiry.inquiry_raw
group by country_name, status_name
having count(*) >= 5;


