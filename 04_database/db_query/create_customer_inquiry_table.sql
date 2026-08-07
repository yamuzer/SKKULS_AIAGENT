/*
새 테이블:
python_lab.customer_inquiry
*/

CREATE TABLE IF NOT EXISTS python_lab.customer_inquiry (
    inquiry_id           VARCHAR(30) PRIMARY KEY,
    source_customer_code VARCHAR(20) NOT NULL,
    customer_id          BIGINT NOT NULL,
    received_at          TIMESTAMP NOT NULL,
    channel              VARCHAR(20) NOT NULL,
    language_code        VARCHAR(10) NOT NULL,
    country_name         VARCHAR(50) NOT NULL,
    inquiry_type         VARCHAR(30) NOT NULL,
    product_code         VARCHAR(30),
    priority             VARCHAR(10) NOT NULL,
    status               VARCHAR(20) NOT NULL,
    response_minutes     INTEGER,
    satisfaction_score   SMALLINT,
    inquiry_text         TEXT NOT NULL,
    needs_follow_up      BOOLEAN NOT NULL,
    sla_limit_minutes    INTEGER NOT NULL,
    sla_breached         BOOLEAN NOT NULL,
    sla_status           VARCHAR(20) NOT NULL,
    loaded_at            TIMESTAMPTZ
                         NOT NULL
                         DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_customer_inquiry_customer
        FOREIGN KEY (customer_id)
        REFERENCES python_lab.customer(customer_id),

    CONSTRAINT ck_customer_inquiry_priority
        CHECK (
            priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')
        ),

    CONSTRAINT ck_customer_inquiry_status
        CHECK (
            status IN (
                'received',
                'in_progress',
                'resolved',
                'closed'
            )
        ),

    CONSTRAINT ck_customer_inquiry_response
        CHECK (
            response_minutes IS NULL
            OR response_minutes >= 0
        ),

    CONSTRAINT ck_customer_inquiry_satisfaction
        CHECK (
            satisfaction_score IS NULL
            OR satisfaction_score BETWEEN 1 AND 5
        ),

    CONSTRAINT ck_customer_inquiry_sla_status
        CHECK (
            sla_status IN ('met', 'pending', 'breached')
        )
);

CREATE INDEX IF NOT EXISTS idx_customer_inquiry_customer
    ON python_lab.customer_inquiry (customer_id);

CREATE INDEX IF NOT EXISTS idx_customer_inquiry_received_at
    ON python_lab.customer_inquiry (received_at);

CREATE INDEX IF NOT EXISTS idx_customer_inquiry_priority_status
    ON python_lab.customer_inquiry (priority, status);

CREATE INDEX IF NOT EXISTS idx_customer_inquiry_follow_up
    ON python_lab.customer_inquiry (
        needs_follow_up,
        sla_breached
    );

SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema = 'python_lab'
  AND table_name = 'customer_inquiry';

SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'python_lab'
  AND table_name = 'customer_inquiry'
ORDER BY ordinal_position;
