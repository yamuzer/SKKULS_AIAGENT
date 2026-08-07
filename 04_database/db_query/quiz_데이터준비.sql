-- ============================================================
-- 실습 1 데이터 준비
-- 해외 고객 문의 데이터 240건을 생성합니다.
-- ============================================================

DROP SCHEMA IF EXISTS review_inquiry CASCADE;
CREATE SCHEMA review_inquiry;

CREATE TABLE review_inquiry.inquiry_raw
(
    inquiry_id         INTEGER PRIMARY KEY,
    customer_id        VARCHAR(10) NOT NULL,
    country_name       VARCHAR(30),
    status_name        VARCHAR(30) NOT NULL,
    channel_name       VARCHAR(30) NOT NULL,
    inquiry_type       VARCHAR(30) NOT NULL,
    priority_name      VARCHAR(20) NOT NULL,
    received_at        TIMESTAMPTZ NOT NULL,
    resolved_at        TIMESTAMPTZ,
    satisfaction_score INTEGER
);

WITH source_data AS
(
    SELECT
        n,
        TIMESTAMPTZ '2026-06-01 08:00:00+09'
            + ((n - 1) % 60) * INTERVAL '1 day'
            + ((n * 37) % 720) * INTERVAL '1 minute' AS received_at
    FROM generate_series(1, 240) AS g(n)
),
prepared_data AS
(
    SELECT
        n AS inquiry_id,
        'C' || LPAD((((n - 1) % 90) + 1)::TEXT, 4, '0') AS customer_id,
        CASE n % 8
            WHEN 0 THEN '대한민국'
            WHEN 1 THEN '미국'
            WHEN 2 THEN '일본'
            WHEN 3 THEN '독일'
            WHEN 4 THEN '프랑스'
            WHEN 5 THEN '싱가포르'
            WHEN 6 THEN '베트남'
            ELSE '캐나다'
        END AS country_name,

        CASE n % 5
            WHEN 0 THEN '접수'
            WHEN 1 THEN '처리중'
            WHEN 2 THEN '고객회신대기'
            WHEN 3 THEN '해결완료'
            ELSE '종결'
        END AS status_name,

        CASE n % 4
            WHEN 0 THEN '이메일'
            WHEN 1 THEN '웹'
            WHEN 2 THEN '전화'
            ELSE '챗봇'
        END AS channel_name,

        CASE n % 6
            WHEN 0 THEN '결제'
            WHEN 1 THEN '배송'
            WHEN 2 THEN '제품사용'
            WHEN 3 THEN '환불'
            WHEN 4 THEN '계정'
            ELSE '기술지원'
        END AS inquiry_type,

        CASE n % 3
            WHEN 0 THEN '높음'
            WHEN 1 THEN '보통'
            ELSE '낮음'
        END AS priority_name,

        received_at
    FROM source_data
)

INSERT INTO review_inquiry.inquiry_raw
(
    inquiry_id,
    customer_id,
    country_name,
    status_name,
    channel_name,
    inquiry_type,
    priority_name,
    received_at,
    resolved_at,
    satisfaction_score
)
SELECT
    inquiry_id,
    customer_id,
    country_name,
    status_name,
    channel_name,
    inquiry_type,
    priority_name,
    received_at,

    CASE
        WHEN status_name IN ('해결완료', '종결')
        THEN received_at + ((inquiry_id % 72) + 2) * INTERVAL '1 hour'
        ELSE NULL
    END AS resolved_at,

    CASE
        WHEN status_name IN ('해결완료', '종결')
        THEN 1 + inquiry_id % 5
        ELSE NULL
    END AS satisfaction_score
FROM prepared_data;

-- 생성 결과 확인
SELECT COUNT(*) AS inquiry_count
FROM review_inquiry.inquiry_raw;

SELECT *
FROM review_inquiry.inquiry_raw
ORDER BY inquiry_id
LIMIT 20;
