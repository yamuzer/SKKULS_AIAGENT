-- ============================================================
-- 고객 문의 품질 파이프라인 PostgreSQL 적재 결과 확인
-- ============================================================
--
-- Database:
--   customer_quality_practice
--
-- Schema:
--   web_inquiry_quality
-- ============================================================


-- 1. 생성된 테이블 확인
SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema = 'web_inquiry_quality'
ORDER BY table_name;


-- 2. 최근 파이프라인 실행 이력
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
FROM web_inquiry_quality.pipeline_run_history
ORDER BY started_at DESC
LIMIT 10;


-- 3. 가장 최근 성공 실행의 적재 건수
WITH latest_run AS (
    SELECT execution_id
    FROM web_inquiry_quality.pipeline_run_history
    WHERE status = 'SUCCESS'
    ORDER BY started_at DESC
    LIMIT 1
)
SELECT
    'web_inquiry_raw' AS table_name,
    COUNT(*) AS row_count
FROM web_inquiry_quality.web_inquiry_raw
WHERE execution_id = (
    SELECT execution_id
    FROM latest_run
)

UNION ALL

SELECT
    'web_inquiry_standardized',
    COUNT(*)
FROM web_inquiry_quality.web_inquiry_standardized
WHERE execution_id = (
    SELECT execution_id
    FROM latest_run
)

UNION ALL

SELECT
    'web_inquiry_valid',
    COUNT(*)
FROM web_inquiry_quality.web_inquiry_valid
WHERE execution_id = (
    SELECT execution_id
    FROM latest_run
)

UNION ALL

SELECT
    'web_inquiry_rejected',
    COUNT(*)
FROM web_inquiry_quality.web_inquiry_rejected
WHERE execution_id = (
    SELECT execution_id
    FROM latest_run
)

UNION ALL

SELECT
    'web_inquiry_quality_issue',
    COUNT(*)
FROM web_inquiry_quality.web_inquiry_quality_issue
WHERE execution_id = (
    SELECT execution_id
    FROM latest_run
);


-- 4. 최근 실행의 규칙별 품질 이슈
WITH latest_run AS (
    SELECT execution_id
    FROM web_inquiry_quality.pipeline_run_history
    WHERE status = 'SUCCESS'
    ORDER BY started_at DESC
    LIMIT 1
)
SELECT
    rule_code,
    COUNT(*) AS issue_count
FROM web_inquiry_quality.web_inquiry_quality_issue
WHERE execution_id = (
    SELECT execution_id
    FROM latest_run
)
GROUP BY rule_code
ORDER BY
    issue_count DESC,
    rule_code;


-- 5. 최근 실행의 오류 고객 문의
WITH latest_run AS (
    SELECT execution_id
    FROM web_inquiry_quality.pipeline_run_history
    WHERE status = 'SUCCESS'
    ORDER BY started_at DESC
    LIMIT 1
)
SELECT
    source_row_number,
    source_inquiry_id,
    posted_at,
    inquiry_type_code,
    priority_code,
    quality_issue_count
FROM web_inquiry_quality.web_inquiry_rejected
WHERE execution_id = (
    SELECT execution_id
    FROM latest_run
)
ORDER BY source_row_number;


-- 6. 오류 고객 문의와 품질 이슈 상세 연결
WITH latest_run AS (
    SELECT execution_id
    FROM web_inquiry_quality.pipeline_run_history
    WHERE status = 'SUCCESS'
    ORDER BY started_at DESC
    LIMIT 1
)
SELECT
    rejected.source_row_number,
    rejected.source_inquiry_id,
    issue.rule_code,
    issue.column_name,
    issue.invalid_value,
    issue.error_message
FROM web_inquiry_quality.web_inquiry_rejected AS rejected
INNER JOIN web_inquiry_quality.web_inquiry_quality_issue AS issue
    ON rejected.execution_id = issue.execution_id
   AND rejected.source_row_number = issue.source_row_number
WHERE rejected.execution_id = (
    SELECT execution_id
    FROM latest_run
)
ORDER BY
    rejected.source_row_number,
    issue.rule_code;
