
BEGIN;

DROP TABLE IF EXISTS python_lab.customer;

CREATE TABLE python_lab.customer (
    customer_id     BIGINT
                    GENERATED ALWAYS AS IDENTITY
                    PRIMARY KEY,
    customer_name   VARCHAR(50)
                    NOT NULL,
    country_name    VARCHAR(50)
                    NOT NULL,
    email           VARCHAR(150)
                    NOT NULL
                    UNIQUE,
    customer_grade  VARCHAR(20)
                    NOT NULL
                    DEFAULT 'BASIC',
    joined_at       DATE
                    NOT NULL
                    DEFAULT CURRENT_DATE,
    is_active       BOOLEAN
                    NOT NULL
                    DEFAULT TRUE,
    created_at      TIMESTAMPTZ
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_customer_grade
        CHECK (
            customer_grade IN (
                'BASIC',
                'SILVER',
                'GOLD'
            )
        )
);

CREATE INDEX idx_customer_country
    ON python_lab.customer (country_name);

CREATE INDEX idx_customer_grade
    ON python_lab.customer (customer_grade);

CREATE INDEX idx_customer_active
    ON python_lab.customer (is_active);

INSERT INTO python_lab.customer (
    customer_name,
    country_name,
    email,
    customer_grade,
    joined_at,
    is_active
)
VALUES
    ('홍지민', 'Germany', 'customer0001@example.com', 'SILVER', '2022-12-12', TRUE),
    ('전성민', 'South Korea', 'customer0002@example.com', 'BASIC', '2025-01-09', TRUE),
    ('전우진', 'Australia', 'customer0003@example.com', 'BASIC', '2022-05-26', TRUE),
    ('윤준호', 'France', 'customer0004@example.com', 'BASIC', '2023-04-09', TRUE),
    ('장도윤', 'Japan', 'customer0005@example.com', 'BASIC', '2024-09-04', TRUE),
    ('서도윤', 'Canada', 'customer0006@example.com', 'SILVER', '2025-10-16', TRUE),
    ('송태현', 'South Korea', 'customer0007@example.com', 'BASIC', '2022-07-21', TRUE),
    ('정하은', 'Singapore', 'customer0008@example.com', 'BASIC', '2023-12-24', FALSE),
    ('황수빈', 'United States', 'customer0009@example.com', 'BASIC', '2022-01-05', TRUE),
    ('홍지훈', 'Australia', 'customer0010@example.com', 'BASIC', '2026-06-11', TRUE),
    ('박예린', 'France', 'customer0011@example.com', 'SILVER', '2024-03-02', TRUE),
    ('윤우진', 'Canada', 'customer0012@example.com', 'BASIC', '2026-04-03', FALSE),
    ('홍하은', 'Germany', 'customer0013@example.com', 'SILVER', '2026-04-26', TRUE),
    ('서승현', 'Canada', 'customer0014@example.com', 'BASIC', '2025-05-14', TRUE),
    ('신하은', 'Canada', 'customer0015@example.com', 'BASIC', '2026-03-10', TRUE),
    ('김태현', 'Japan', 'customer0016@example.com', 'BASIC', '2024-03-03', TRUE),
    ('최수빈', 'Australia', 'customer0017@example.com', 'BASIC', '2025-05-27', FALSE),
    ('황민준', 'Germany', 'customer0018@example.com', 'SILVER', '2025-05-21', TRUE),
    ('최성민', 'Australia', 'customer0019@example.com', 'SILVER', '2023-10-22', TRUE),
    ('한하은', 'Canada', 'customer0020@example.com', 'BASIC', '2026-04-24', TRUE),
    ('서소윤', 'Germany', 'customer0021@example.com', 'BASIC', '2024-11-08', TRUE),
    ('최수빈', 'South Korea', 'customer0022@example.com', 'BASIC', '2024-08-21', TRUE),
    ('임예린', 'Japan', 'customer0023@example.com', 'BASIC', '2022-08-22', TRUE),
    ('서민서', 'South Korea', 'customer0024@example.com', 'BASIC', '2022-08-16', TRUE),
    ('김유진', 'South Korea', 'customer0025@example.com', 'SILVER', '2024-01-12', TRUE),
    ('전수빈', 'Australia', 'customer0026@example.com', 'BASIC', '2026-01-29', TRUE),
    ('서하은', 'Singapore', 'customer0027@example.com', 'BASIC', '2026-01-06', TRUE),
    ('임채원', 'Japan', 'customer0028@example.com', 'BASIC', '2022-07-11', FALSE),
    ('송민서', 'South Korea', 'customer0029@example.com', 'BASIC', '2023-11-15', TRUE),
    ('이민서', 'France', 'customer0030@example.com', 'BASIC', '2022-06-29', TRUE),
    ('임유진', 'Canada', 'customer0031@example.com', 'SILVER', '2022-06-13', TRUE),
    ('황승현', 'Singapore', 'customer0032@example.com', 'SILVER', '2022-09-29', TRUE),
    ('강다은', 'Germany', 'customer0033@example.com', 'GOLD', '2024-10-20', FALSE),
    ('윤채원', 'France', 'customer0034@example.com', 'BASIC', '2022-12-12', TRUE),
    ('한현우', 'United States', 'customer0035@example.com', 'BASIC', '2024-12-02', TRUE),
    ('권유진', 'Singapore', 'customer0036@example.com', 'BASIC', '2025-03-26', TRUE),
    ('박예린', 'Canada', 'customer0037@example.com', 'BASIC', '2024-06-04', TRUE),
    ('김승현', 'Japan', 'customer0038@example.com', 'BASIC', '2022-12-06', TRUE),
    ('정우진', 'Germany', 'customer0039@example.com', 'GOLD', '2025-08-14', TRUE),
    ('신하은', 'France', 'customer0040@example.com', 'BASIC', '2024-03-04', TRUE),
    ('김소윤', 'Germany', 'customer0041@example.com', 'BASIC', '2022-05-23', TRUE),
    ('최태현', 'South Korea', 'customer0042@example.com', 'BASIC', '2023-03-09', TRUE),
    ('황수빈', 'United States', 'customer0043@example.com', 'BASIC', '2022-10-15', TRUE),
    ('홍채원', 'Singapore', 'customer0044@example.com', 'BASIC', '2025-02-04', TRUE),
    ('서나연', 'Canada', 'customer0045@example.com', 'BASIC', '2023-01-21', FALSE),
    ('임우진', 'Australia', 'customer0046@example.com', 'SILVER', '2026-01-12', TRUE),
    ('정채원', 'Germany', 'customer0047@example.com', 'BASIC', '2026-03-07', TRUE),
    ('송채원', 'South Korea', 'customer0048@example.com', 'BASIC', '2022-09-26', TRUE),
    ('서성민', 'Japan', 'customer0049@example.com', 'GOLD', '2024-04-15', TRUE),
    ('안지훈', 'France', 'customer0050@example.com', 'BASIC', '2024-02-27', TRUE),
    ('신수빈', 'Australia', 'customer0051@example.com', 'SILVER', '2023-12-25', TRUE),
    ('서예린', 'Australia', 'customer0052@example.com', 'BASIC', '2024-11-17', TRUE),
    ('홍서연', 'France', 'customer0053@example.com', 'BASIC', '2023-05-12', TRUE),
    ('최소윤', 'France', 'customer0054@example.com', 'BASIC', '2022-04-16', TRUE),
    ('박다은', 'Japan', 'customer0055@example.com', 'BASIC', '2024-03-21', TRUE),
    ('강다은', 'Singapore', 'customer0056@example.com', 'SILVER', '2022-12-28', TRUE),
    ('오하은', 'South Korea', 'customer0057@example.com', 'BASIC', '2022-08-26', TRUE),
    ('김성민', 'United States', 'customer0058@example.com', 'GOLD', '2024-02-09', TRUE),
    ('황민준', 'Canada', 'customer0059@example.com', 'SILVER', '2022-03-30', TRUE),
    ('송유진', 'Canada', 'customer0060@example.com', 'BASIC', '2022-08-14', TRUE),
    ('박현우', 'Japan', 'customer0061@example.com', 'BASIC', '2025-12-21', TRUE),
    ('서민준', 'Australia', 'customer0062@example.com', 'SILVER', '2025-12-25', TRUE),
    ('신민준', 'Japan', 'customer0063@example.com', 'BASIC', '2022-08-13', TRUE),
    ('김하은', 'Canada', 'customer0064@example.com', 'BASIC', '2024-12-13', TRUE),
    ('권유진', 'Japan', 'customer0065@example.com', 'BASIC', '2024-03-17', TRUE),
    ('서승현', 'United States', 'customer0066@example.com', 'BASIC', '2022-03-11', TRUE),
    ('오민서', 'Australia', 'customer0067@example.com', 'GOLD', '2024-03-08', TRUE),
    ('임나연', 'Japan', 'customer0068@example.com', 'GOLD', '2025-06-08', TRUE),
    ('황준호', 'Canada', 'customer0069@example.com', 'BASIC', '2024-03-21', TRUE),
    ('임성민', 'United States', 'customer0070@example.com', 'GOLD', '2026-04-10', TRUE),
    ('윤현우', 'United States', 'customer0071@example.com', 'BASIC', '2023-01-15', TRUE),
    ('이유진', 'South Korea', 'customer0072@example.com', 'BASIC', '2025-02-19', TRUE),
    ('오소윤', 'Singapore', 'customer0073@example.com', 'BASIC', '2022-12-15', TRUE),
    ('송승현', 'Australia', 'customer0074@example.com', 'BASIC', '2022-05-15', TRUE),
    ('오성민', 'Germany', 'customer0075@example.com', 'BASIC', '2022-08-26', TRUE),
    ('송민준', 'Japan', 'customer0076@example.com', 'BASIC', '2025-07-27', TRUE),
    ('한성민', 'Japan', 'customer0077@example.com', 'BASIC', '2025-08-16', FALSE),
    ('장민준', 'France', 'customer0078@example.com', 'GOLD', '2023-11-10', TRUE),
    ('김민준', 'Australia', 'customer0079@example.com', 'BASIC', '2024-08-25', TRUE),
    ('송현우', 'Australia', 'customer0080@example.com', 'BASIC', '2022-09-30', TRUE),
    ('홍도윤', 'South Korea', 'customer0081@example.com', 'BASIC', '2022-06-01', TRUE),
    ('오성민', 'Singapore', 'customer0082@example.com', 'BASIC', '2024-02-27', TRUE),
    ('신민서', 'Japan', 'customer0083@example.com', 'BASIC', '2023-07-05', TRUE),
    ('전민서', 'France', 'customer0084@example.com', 'SILVER', '2026-01-14', TRUE),
    ('조성민', 'Australia', 'customer0085@example.com', 'BASIC', '2023-11-29', TRUE),
    ('최유진', 'Singapore', 'customer0086@example.com', 'BASIC', '2024-04-05', TRUE),
    ('황태현', 'Japan', 'customer0087@example.com', 'BASIC', '2026-05-27', TRUE),
    ('김우진', 'Australia', 'customer0088@example.com', 'BASIC', '2024-02-21', TRUE),
    ('한서연', 'Japan', 'customer0089@example.com', 'BASIC', '2022-10-20', TRUE),
    ('전현우', 'Australia', 'customer0090@example.com', 'GOLD', '2024-12-17', TRUE),
    ('장도윤', 'United States', 'customer0091@example.com', 'BASIC', '2022-07-03', TRUE),
    ('최승현', 'United States', 'customer0092@example.com', 'SILVER', '2024-07-16', TRUE),
    ('강승현', 'France', 'customer0093@example.com', 'GOLD', '2022-03-08', TRUE),
    ('박수빈', 'South Korea', 'customer0094@example.com', 'SILVER', '2023-08-26', TRUE),
    ('송성민', 'Germany', 'customer0095@example.com', 'BASIC', '2023-11-02', TRUE),
    ('윤민서', 'France', 'customer0096@example.com', 'BASIC', '2025-11-15', TRUE),
    ('송도윤', 'France', 'customer0097@example.com', 'BASIC', '2022-10-05', TRUE),
    ('권소윤', 'Japan', 'customer0098@example.com', 'BASIC', '2025-08-03', TRUE),
    ('이유진', 'Australia', 'customer0099@example.com', 'GOLD', '2024-01-13', TRUE),
    ('정채원', 'Japan', 'customer0100@example.com', 'SILVER', '2025-02-04', TRUE),
    ('전성민', 'Singapore', 'customer0101@example.com', 'BASIC', '2022-02-07', TRUE),
    ('임예린', 'Japan', 'customer0102@example.com', 'BASIC', '2023-12-01', FALSE),
    ('윤성민', 'South Korea', 'customer0103@example.com', 'GOLD', '2026-06-03', TRUE),
    ('권준호', 'Japan', 'customer0104@example.com', 'BASIC', '2026-06-14', TRUE),
    ('김민준', 'United States', 'customer0105@example.com', 'SILVER', '2022-04-01', TRUE),
    ('윤채원', 'Canada', 'customer0106@example.com', 'BASIC', '2024-10-06', TRUE),
    ('임민준', 'Japan', 'customer0107@example.com', 'BASIC', '2025-07-11', FALSE),
    ('박수빈', 'United States', 'customer0108@example.com', 'SILVER', '2025-06-20', TRUE),
    ('김승현', 'Canada', 'customer0109@example.com', 'BASIC', '2024-11-10', TRUE),
    ('최채원', 'Australia', 'customer0110@example.com', 'BASIC', '2025-01-10', TRUE),
    ('정소윤', 'South Korea', 'customer0111@example.com', 'SILVER', '2023-01-22', TRUE),
    ('홍도윤', 'United States', 'customer0112@example.com', 'BASIC', '2024-01-04', FALSE),
    ('윤현우', 'United States', 'customer0113@example.com', 'BASIC', '2022-09-19', TRUE),
    ('임우진', 'Singapore', 'customer0114@example.com', 'BASIC', '2025-07-24', TRUE),
    ('신성민', 'France', 'customer0115@example.com', 'BASIC', '2023-10-30', TRUE),
    ('임서연', 'Canada', 'customer0116@example.com', 'BASIC', '2025-09-14', TRUE),
    ('윤하은', 'Germany', 'customer0117@example.com', 'BASIC', '2023-04-28', TRUE),
    ('전우진', 'United States', 'customer0118@example.com', 'SILVER', '2023-10-11', TRUE),
    ('송예린', 'Canada', 'customer0119@example.com', 'BASIC', '2025-04-24', TRUE),
    ('조서연', 'South Korea', 'customer0120@example.com', 'BASIC', '2022-12-01', TRUE);

COMMIT;


/*
============================================================
입력 결과 확인
============================================================
*/

SELECT
    COUNT(*) AS customer_count
FROM python_lab.customer;

SELECT
    customer_grade,
    COUNT(*) AS customer_count
FROM python_lab.customer
GROUP BY customer_grade
ORDER BY customer_grade;

SELECT
    customer_id,
    customer_name,
    country_name,
    email,
    customer_grade,
    joined_at,
    is_active,
    created_at
FROM python_lab.customer
ORDER BY customer_id
LIMIT 10;
