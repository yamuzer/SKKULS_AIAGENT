

DROP SCHEMA IF EXISTS join_basic CASCADE;

CREATE SCHEMA join_basic;


-- -----------------------------------------------------------
-- 1. 부서 테이블
-- -----------------------------------------------------------

CREATE TABLE join_basic.department (
    department_id   INTEGER      PRIMARY KEY,
    department_name VARCHAR(50)  NOT NULL
);


-- -----------------------------------------------------------
-- 2. 직원 테이블
--
-- department_id는 NULL을 허용합니다.
-- 아직 부서가 배정되지 않은 직원도 저장하기 위해서입니다.
-- -----------------------------------------------------------

CREATE TABLE join_basic.employee (
    employee_id     INTEGER      PRIMARY KEY,
    employee_name   VARCHAR(50)  NOT NULL,
    department_id   INTEGER,
    salary          INTEGER      NOT NULL,
    CONSTRAINT fk_employee_department
        FOREIGN KEY (department_id)
        REFERENCES join_basic.department(department_id)
);


-- -----------------------------------------------------------
-- 3. 근무조 테이블
--
-- CROSS JOIN 연습에만 사용합니다.
-- -----------------------------------------------------------

CREATE TABLE join_basic.work_shift (
    shift_code VARCHAR(10) PRIMARY KEY,
    shift_name VARCHAR(30) NOT NULL
);


-- -----------------------------------------------------------
-- 4. 부서 데이터 입력
--
-- 인사팀에는 직원이 없습니다.
-- -----------------------------------------------------------

INSERT INTO join_basic.department (
    department_id,
    department_name
)
VALUES
    (10, '데이터팀'),
    (20, 'AI팀'),
    (30, '영업팀'),
    (40, '인사팀');


-- -----------------------------------------------------------
-- 5. 직원 데이터 입력
--
-- 정수빈은 department_id가 NULL입니다.
-- 즉, 아직 부서가 배정되지 않은 직원입니다.
-- -----------------------------------------------------------

INSERT INTO join_basic.employee (
    employee_id,
    employee_name,
    department_id,
    salary
)
VALUES
    (101, '김민지', 10, 4200000),
    (102, '이준호', 10, 3900000),
    (103, '박서연', 20, 4700000),
    (104, '최현우', 30, 4100000),
    (105, '정수빈', NULL, 3500000);


-- -----------------------------------------------------------
-- 6. 근무조 데이터 입력
-- -----------------------------------------------------------

INSERT INTO join_basic.work_shift (
    shift_code,
    shift_name
)
VALUES
    ('DAY', '주간조'),
    ('NIGHT', '야간조');


-- -----------------------------------------------------------
-- 7. 입력 결과 확인
-- -----------------------------------------------------------

SELECT *
FROM join_basic.department
ORDER BY department_id;

SELECT *
FROM join_basic.employee
ORDER BY employee_id;

SELECT *
FROM join_basic.work_shift
ORDER BY shift_code;
