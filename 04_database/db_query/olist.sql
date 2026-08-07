CREATE TABLE olist_customers (
    customer_id              CHAR(32) PRIMARY KEY,
    customer_unique_id       CHAR(32) NOT NULL,
    customer_zip_code_prefix VARCHAR(5) NOT NULL,
    customer_city            VARCHAR(100) NOT NULL,
    customer_state           CHAR(2) NOT NULL
);


CREATE TABLE olist_orders (
    order_id                       CHAR(32) PRIMARY KEY,
    customer_id                    CHAR(32) NOT NULL,
    order_status                   VARCHAR(20) NOT NULL,
    order_purchase_timestamp       TIMESTAMP NOT NULL,
    order_approved_at              TIMESTAMP,
    order_delivered_carrier_date   TIMESTAMP,
    order_delivered_customer_date  TIMESTAMP,
    order_estimated_delivery_date  TIMESTAMP NOT NULL,

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES olist_customers (customer_id)
);