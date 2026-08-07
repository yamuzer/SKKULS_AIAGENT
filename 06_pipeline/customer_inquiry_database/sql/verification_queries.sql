
-- 1. 최근 실행 이력
SELECT
    execution_id,
    started_at,
    completed_at,
    status,
    raw_count,
    standardized_count,
    valid_count,
    invalid_count,
    issue_count,
    error_message
FROM customer_quality.quality_execution_history
ORDER BY started_at DESC
LIMIT 10;


-- 2. 최근 성공 실행의 execution_id
WITH latest_execution AS (
    SELECT execution_id
    FROM customer_quality.quality_execution_history
    WHERE status = 'SUCCESS'
    ORDER BY started_at DESC
    LIMIT 1
)
SELECT
    'raw' AS data_stage,
    COUNT(*) AS row_count
FROM customer_quality.customer_inquiry_raw
WHERE execution_id = (
    SELECT execution_id
    FROM latest_execution
)

UNION ALL

SELECT
    'standardized',
    COUNT(*)
FROM customer_quality.customer_inquiry_standardized
WHERE execution_id = (
    SELECT execution_id
    FROM latest_execution
)

UNION ALL

SELECT
    'valid',
    COUNT(*)
FROM customer_quality.customer_inquiry_valid
WHERE execution_id = (
    SELECT execution_id
    FROM latest_execution
)

UNION ALL

SELECT
    'invalid',
    COUNT(*)
FROM customer_quality.customer_inquiry_invalid
WHERE execution_id = (
    SELECT execution_id
    FROM latest_execution
)

UNION ALL

SELECT
    'quality_issue',
    COUNT(*)
FROM customer_quality.customer_inquiry_quality_issue
WHERE execution_id = (
    SELECT execution_id
    FROM latest_execution
);


-- 3. 최근 실행의 규칙별 오류 건수
WITH latest_execution AS (
    SELECT execution_id
    FROM customer_quality.quality_execution_history
    WHERE status = 'SUCCESS'
    ORDER BY started_at DESC
    LIMIT 1
)
SELECT
    rule_code,
    COUNT(*) AS issue_count
FROM customer_quality.customer_inquiry_quality_issue
WHERE execution_id = (
    SELECT execution_id
    FROM latest_execution
)
GROUP BY rule_code
ORDER BY
    issue_count DESC,
    rule_code;


-- 4. 최근 실행의 오류 고객 문의
WITH latest_execution AS (
    SELECT execution_id
    FROM customer_quality.quality_execution_history
    WHERE status = 'SUCCESS'
    ORDER BY started_at DESC
    LIMIT 1
)
SELECT
    source_inquiry_id,
    posted_at_raw,
    inquiry_type_raw,
    priority_raw,
    quality_issue_count
FROM customer_quality.customer_inquiry_invalid
WHERE execution_id = (
    SELECT execution_id
    FROM latest_execution
)
ORDER BY source_row_number;
