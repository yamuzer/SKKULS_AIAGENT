DROP SCHEMA IF EXISTS sqlalchemy_review CASCADE;
CREATE SCHEMA sqlalchemy_review;

CREATE TABLE sqlalchemy_review.customer
(
    customer_id     INTEGER PRIMARY KEY,
    customer_code   VARCHAR(20) NOT NULL UNIQUE,
    customer_name   VARCHAR(100) NOT NULL,
    customer_grade  VARCHAR(20) NOT NULL,
    country_name    VARCHAR(50) NOT NULL
);

CREATE TABLE sqlalchemy_review.customer_inquiry
(
    inquiry_id          VARCHAR(30) PRIMARY KEY,
    source_customer_code VARCHAR(30) NOT NULL,
    customer_id         INTEGER NOT NULL
                        REFERENCES sqlalchemy_review.customer(customer_id),
    received_at         TIMESTAMPTZ NOT NULL,
    channel             VARCHAR(30) NOT NULL,
    language_code       VARCHAR(10) NOT NULL,
    country_name        VARCHAR(50) NOT NULL,
    inquiry_type        VARCHAR(30) NOT NULL,
    product_code        VARCHAR(30),
    priority            VARCHAR(20) NOT NULL,
    status              VARCHAR(30) NOT NULL,
    response_minutes    INTEGER,
    satisfaction_score  INTEGER,
    inquiry_text        TEXT NOT NULL,
    needs_follow_up     BOOLEAN NOT NULL,
    sla_limit_minutes   INTEGER NOT NULL,
    sla_breached        BOOLEAN NOT NULL,
    sla_status          VARCHAR(20) NOT NULL,
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_customer_inquiry_customer_id
    ON sqlalchemy_review.customer_inquiry(customer_id);

CREATE INDEX ix_customer_inquiry_received_at
    ON sqlalchemy_review.customer_inquiry(received_at);
