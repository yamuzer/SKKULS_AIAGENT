CREATE DATABASE python_postgresql_lab
	WITH
	ENCODING = 'UTF8'
	TEMPLATE = template0;
/*

실행 위치:
- python_postgresql_lab 데이터베이스의 Query Tool

실행 내용:
1. python_lab 스키마 생성
2. department 테이블 생성
3. employee 테이블 생성
4. 부서 8건 입력
5. 직원 200건 입력
============================================================
*/




BEGIN;

DROP SCHEMA IF EXISTS python_lab CASCADE;

CREATE SCHEMA python_lab;

CREATE TABLE python_lab.department (
    department_id   INTEGER      PRIMARY KEY,
    department_name VARCHAR(50)  NOT NULL UNIQUE,
    location_name   VARCHAR(50)  NOT NULL
);

CREATE TABLE python_lab.employee (
    employee_id       INTEGER       PRIMARY KEY,
    employee_name     VARCHAR(50)   NOT NULL,
    department_id     INTEGER,
    job_title         VARCHAR(100)  NOT NULL,
    salary            INTEGER       NOT NULL,
    hire_date         DATE          NOT NULL,
    employment_status VARCHAR(20)   NOT NULL,
    country_name      VARCHAR(50)   NOT NULL,
    email             VARCHAR(150)  NOT NULL UNIQUE,
    CONSTRAINT fk_employee_department
        FOREIGN KEY (department_id)
        REFERENCES python_lab.department(department_id),
    CONSTRAINT ck_employee_salary
        CHECK (salary > 0),
    CONSTRAINT ck_employee_status
        CHECK (
            employment_status IN ('active', 'leave', 'retired')
        )
);

CREATE INDEX idx_employee_department_id
    ON python_lab.employee (department_id);

CREATE INDEX idx_employee_status
    ON python_lab.employee (employment_status);

CREATE INDEX idx_employee_hire_date
    ON python_lab.employee (hire_date);

INSERT INTO python_lab.department (
    department_id,
    department_name,
    location_name
)
VALUES
    (10, '데이터분석팀', '서울'),
    (20, 'AI연구팀', '서울'),
    (30, '고객지원팀', '부산'),
    (40, '영업팀', '대전'),
    (50, '인사팀', '서울'),
    (60, '마케팅팀', '인천'),
    (70, '재무팀', '서울'),
    (80, '해외사업팀', '제주');

INSERT INTO python_lab.employee (
    employee_id,
    employee_name,
    department_id,
    job_title,
    salary,
    hire_date,
    employment_status,
    country_name,
    email
)
VALUES
    (1001, '홍지민', 10, '데이터엔지니어', 6200000, '2019-11-23', 'active', 'Singapore', 'employee1001@example.com'),
    (1002, '송우진', 20, 'AI엔지니어', 5000000, '2024-01-19', 'active', 'Germany', 'employee1002@example.com'),
    (1003, '오지훈', 30, 'VOC분석가', 4800000, '2022-01-12', 'active', 'South Korea', 'employee1003@example.com'),
    (1004, '서하은', 40, '영업기획자', 4000000, '2025-10-15', 'active', 'Germany', 'employee1004@example.com'),
    (1005, '서성민', 50, '교육담당자', 4600000, '2022-06-07', 'active', 'Germany', 'employee1005@example.com'),
    (1006, '이예린', 60, '마케팅담당자', 3600000, '2019-06-03', 'active', 'South Korea', 'employee1006@example.com'),
    (1007, '장예린', 70, '재무팀장', 6300000, '2020-01-28', 'active', 'South Korea', 'employee1007@example.com'),
    (1008, '오소윤', 80, '해외영업담당', 4900000, '2022-02-21', 'active', 'South Korea', 'employee1008@example.com'),
    (1009, '오민서', 10, '분석팀장', 7200000, '2021-09-26', 'active', 'Singapore', 'employee1009@example.com'),
    (1010, '이소윤', 20, 'AI연구원', 5100000, '2022-05-30', 'active', 'Singapore', 'employee1010@example.com'),
    (1011, '안성민', 30, 'VOC분석가', 5800000, '2026-04-21', 'active', 'Singapore', 'employee1011@example.com'),
    (1012, '장성민', 40, '영업담당자', 3700000, '2018-02-02', 'active', 'South Korea', 'employee1012@example.com'),
    (1013, '윤성민', 50, '인사담당자', 3600000, '2023-05-22', 'active', 'Germany', 'employee1013@example.com'),
    (1014, '김하은', 60, '마케팅팀장', 6800000, '2025-05-10', 'active', 'Singapore', 'employee1014@example.com'),
    (1015, '권태현', 70, '예산분석가', 4500000, '2025-10-15', 'active', 'Japan', 'employee1015@example.com'),
    (1016, '신도윤', 80, '해외사업팀장', 7200000, '2024-10-24', 'active', 'South Korea', 'employee1016@example.com'),
    (1017, '안민서', 10, '데이터분석가', 4200000, '2023-10-07', 'active', 'South Korea', 'employee1017@example.com'),
    (1018, '황예린', 20, 'AI연구원', 5400000, '2019-01-21', 'active', 'South Korea', 'employee1018@example.com'),
    (1019, '오성민', 30, '품질관리자', 4200000, '2021-08-23', 'active', 'South Korea', 'employee1019@example.com'),
    (1020, '김유진', NULL, '프로젝트지원담당', 3500000, '2025-12-06', 'leave', 'United States', 'employee1020@example.com'),
    (1021, '송우진', 50, '인사담당자', 4700000, '2019-11-18', 'active', 'Singapore', 'employee1021@example.com'),
    (1022, '장도윤', 60, '마케팅담당자', 3800000, '2021-04-22', 'active', 'South Korea', 'employee1022@example.com'),
    (1023, '윤지훈', 70, '예산분석가', 4000000, '2018-08-19', 'active', 'Singapore', 'employee1023@example.com'),
    (1024, '이민서', 80, '파트너관리자', 4800000, '2018-12-25', 'active', 'Japan', 'employee1024@example.com'),
    (1025, '조채원', 10, '데이터분석가', 5900000, '2025-07-15', 'active', 'Germany', 'employee1025@example.com'),
    (1026, '안유진', 20, 'ML엔지니어', 5500000, '2019-12-23', 'active', 'Japan', 'employee1026@example.com'),
    (1027, '홍다은', 30, 'VOC분석가', 5200000, '2022-03-08', 'active', 'South Korea', 'employee1027@example.com'),
    (1028, '최민서', 40, '영업기획자', 4200000, '2025-11-19', 'active', 'South Korea', 'employee1028@example.com'),
    (1029, '권유진', 50, '교육담당자', 3700000, '2024-06-19', 'active', 'South Korea', 'employee1029@example.com'),
    (1030, '오우진', 60, '마케팅팀장', 6600000, '2022-11-06', 'active', 'South Korea', 'employee1030@example.com'),
    (1031, '안지훈', 70, '예산분석가', 4400000, '2023-04-08', 'active', 'Japan', 'employee1031@example.com'),
    (1032, '홍채원', 80, '해외사업팀장', 6800000, '2021-09-10', 'active', 'Singapore', 'employee1032@example.com'),
    (1033, '김민준', 10, '데이터엔지니어', 4500000, '2018-10-13', 'active', 'South Korea', 'employee1033@example.com'),
    (1034, '권서연', 20, 'AI엔지니어', 5100000, '2018-08-05', 'active', 'South Korea', 'employee1034@example.com'),
    (1035, '정서연', 30, 'VOC분석가', 4900000, '2024-10-08', 'active', 'South Korea', 'employee1035@example.com'),
    (1036, '김나연', 40, '영업담당자', 4500000, '2024-01-23', 'active', 'United States', 'employee1036@example.com'),
    (1037, '조우진', 50, '채용담당자', 5100000, '2023-07-20', 'leave', 'South Korea', 'employee1037@example.com'),
    (1038, '정채원', 60, '시장분석가', 4600000, '2026-05-12', 'active', 'Singapore', 'employee1038@example.com'),
    (1039, '전소윤', 70, '재무담당자', 3600000, '2019-06-22', 'leave', 'Singapore', 'employee1039@example.com'),
    (1040, '서지훈', NULL, '프로젝트지원담당', 4700000, '2023-08-05', 'leave', 'South Korea', 'employee1040@example.com'),
    (1041, '한지훈', 10, '분석팀장', 6100000, '2022-10-04', 'active', 'Germany', 'employee1041@example.com'),
    (1042, '송예린', 20, 'ML엔지니어', 5700000, '2022-01-04', 'leave', 'Germany', 'employee1042@example.com'),
    (1043, '정승현', 30, '품질관리자', 4200000, '2021-12-05', 'active', 'South Korea', 'employee1043@example.com'),
    (1044, '한수빈', 40, '고객관리자', 4300000, '2018-07-30', 'active', 'South Korea', 'employee1044@example.com'),
    (1045, '황수빈', 50, '채용담당자', 4500000, '2026-02-12', 'active', 'South Korea', 'employee1045@example.com'),
    (1046, '황유진', 60, '콘텐츠기획자', 5300000, '2022-02-03', 'active', 'South Korea', 'employee1046@example.com'),
    (1047, '강수빈', 70, '재무팀장', 6000000, '2022-05-27', 'active', 'Singapore', 'employee1047@example.com'),
    (1048, '임다은', 80, '해외영업담당', 4600000, '2023-03-10', 'active', 'South Korea', 'employee1048@example.com'),
    (1049, '송유진', 10, '분석팀장', 6500000, '2019-03-28', 'active', 'South Korea', 'employee1049@example.com'),
    (1050, '정지훈', 20, 'AI연구원', 6500000, '2022-08-06', 'active', 'South Korea', 'employee1050@example.com'),
    (1051, '권성민', 30, 'VOC분석가', 5200000, '2018-01-30', 'active', 'South Korea', 'employee1051@example.com'),
    (1052, '최현우', 40, '영업담당자', 4100000, '2022-10-11', 'active', 'Germany', 'employee1052@example.com'),
    (1053, '권유진', 50, '인사담당자', 4200000, '2022-06-02', 'active', 'Singapore', 'employee1053@example.com'),
    (1054, '안현우', 60, '시장분석가', 4000000, '2018-01-10', 'active', 'United States', 'employee1054@example.com'),
    (1055, '권소윤', 70, '재무팀장', 7500000, '2021-03-28', 'leave', 'South Korea', 'employee1055@example.com'),
    (1056, '전소윤', 80, '지역전략담당', 4900000, '2026-06-15', 'active', 'Singapore', 'employee1056@example.com'),
    (1057, '장성민', 10, '데이터분석가', 4800000, '2022-06-04', 'active', 'South Korea', 'employee1057@example.com'),
    (1058, '윤현우', 20, 'ML엔지니어', 6600000, '2021-07-23', 'active', 'Singapore', 'employee1058@example.com'),
    (1059, '이유진', 30, '고객상담원', 3200000, '2024-04-09', 'leave', 'United States', 'employee1059@example.com'),
    (1060, '홍도윤', NULL, '프로젝트지원담당', 3800000, '2019-11-29', 'active', 'Germany', 'employee1060@example.com'),
    (1061, '오지훈', 50, '인사팀장', 7100000, '2022-04-23', 'active', 'South Korea', 'employee1061@example.com'),
    (1062, '최도윤', 60, '마케팅담당자', 3500000, '2025-02-15', 'active', 'South Korea', 'employee1062@example.com'),
    (1063, '한성민', 70, '재무담당자', 4400000, '2025-04-01', 'leave', 'Japan', 'employee1063@example.com'),
    (1064, '김민서', 80, '파트너관리자', 5800000, '2018-02-09', 'active', 'Germany', 'employee1064@example.com'),
    (1065, '이다은', 10, '분석팀장', 7700000, '2019-07-06', 'active', 'United States', 'employee1065@example.com'),
    (1066, '정도윤', 20, 'ML엔지니어', 4500000, '2018-07-21', 'active', 'South Korea', 'employee1066@example.com'),
    (1067, '오성민', 30, 'VOC분석가', 4000000, '2022-04-24', 'active', 'Singapore', 'employee1067@example.com'),
    (1068, '한지훈', 40, '영업담당자', 4100000, '2018-08-05', 'leave', 'United States', 'employee1068@example.com'),
    (1069, '한태현', 50, '인사담당자', 3900000, '2022-04-23', 'active', 'United States', 'employee1069@example.com'),
    (1070, '한다은', 60, '마케팅담당자', 3900000, '2020-04-02', 'active', 'Singapore', 'employee1070@example.com'),
    (1071, '강다은', 70, '재무팀장', 6300000, '2021-09-25', 'active', 'South Korea', 'employee1071@example.com'),
    (1072, '전다은', 80, '해외영업담당', 4600000, '2020-08-30', 'active', 'South Korea', 'employee1072@example.com'),
    (1073, '안수빈', 10, '데이터분석가', 4300000, '2022-04-18', 'leave', 'South Korea', 'employee1073@example.com'),
    (1074, '권우진', 20, 'AI연구원', 5000000, '2019-08-23', 'active', 'South Korea', 'employee1074@example.com'),
    (1075, '신수빈', 30, 'VOC분석가', 5300000, '2023-01-29', 'active', 'South Korea', 'employee1075@example.com'),
    (1076, '안민서', 40, '영업담당자', 5000000, '2018-10-07', 'active', 'South Korea', 'employee1076@example.com'),
    (1077, '권준호', 50, '채용담당자', 5000000, '2022-04-05', 'active', 'Japan', 'employee1077@example.com'),
    (1078, '한지훈', 60, '콘텐츠기획자', 4800000, '2022-03-14', 'active', 'South Korea', 'employee1078@example.com'),
    (1079, '송도윤', 70, '예산분석가', 4500000, '2019-07-09', 'active', 'Germany', 'employee1079@example.com'),
    (1080, '홍소윤', NULL, '프로젝트지원담당', 3600000, '2019-06-21', 'active', 'South Korea', 'employee1080@example.com'),
    (1081, '조우진', 10, '분석팀장', 7800000, '2022-01-24', 'leave', 'South Korea', 'employee1081@example.com'),
    (1082, '신승현', 20, 'AI엔지니어', 6600000, '2022-08-22', 'leave', 'United States', 'employee1082@example.com'),
    (1083, '전성민', 30, 'VOC분석가', 4600000, '2018-03-16', 'leave', 'Japan', 'employee1083@example.com'),
    (1084, '오지훈', 40, '영업담당자', 4300000, '2024-06-19', 'active', 'Singapore', 'employee1084@example.com'),
    (1085, '이우진', 50, '인사팀장', 7400000, '2021-04-20', 'active', 'South Korea', 'employee1085@example.com'),
    (1086, '송민준', 60, '마케팅담당자', 3800000, '2023-10-24', 'active', 'South Korea', 'employee1086@example.com'),
    (1087, '신소윤', 70, '재무팀장', 6200000, '2023-07-12', 'active', 'Japan', 'employee1087@example.com'),
    (1088, '김지훈', 80, '파트너관리자', 4300000, '2019-02-12', 'active', 'Germany', 'employee1088@example.com'),
    (1089, '김승현', 10, '분석팀장', 6500000, '2023-09-20', 'active', 'South Korea', 'employee1089@example.com'),
    (1090, '신태현', 20, 'AI연구원', 6000000, '2019-11-29', 'active', 'South Korea', 'employee1090@example.com'),
    (1091, '안유진', 30, '품질관리자', 4800000, '2023-11-03', 'active', 'South Korea', 'employee1091@example.com'),
    (1092, '오소윤', 40, '영업기획자', 4200000, '2024-10-21', 'active', 'South Korea', 'employee1092@example.com'),
    (1093, '정유진', 50, '채용담당자', 5100000, '2026-03-10', 'active', 'South Korea', 'employee1093@example.com'),
    (1094, '윤채원', 60, '마케팅팀장', 7100000, '2022-02-24', 'active', 'Japan', 'employee1094@example.com'),
    (1095, '임서연', 70, '재무팀장', 6600000, '2025-05-29', 'active', 'South Korea', 'employee1095@example.com'),
    (1096, '장하은', 80, '지역전략담당', 4100000, '2021-12-12', 'leave', 'South Korea', 'employee1096@example.com'),
    (1097, '황민서', 10, '데이터엔지니어', 6600000, '2024-01-15', 'active', 'Singapore', 'employee1097@example.com'),
    (1098, '정우진', 20, 'ML엔지니어', 5100000, '2018-05-31', 'active', 'United States', 'employee1098@example.com'),
    (1099, '강도윤', 30, '품질관리자', 5000000, '2020-12-11', 'active', 'South Korea', 'employee1099@example.com'),
    (1100, '박승현', NULL, '프로젝트지원담당', 5000000, '2024-06-14', 'active', 'Germany', 'employee1100@example.com'),
    (1101, '황채원', 50, '채용담당자', 3600000, '2020-02-29', 'active', 'South Korea', 'employee1101@example.com'),
    (1102, '홍유진', 60, '마케팅담당자', 4700000, '2020-06-08', 'active', 'South Korea', 'employee1102@example.com'),
    (1103, '장예린', 70, '회계담당자', 4300000, '2021-12-31', 'active', 'United States', 'employee1103@example.com'),
    (1104, '권현우', 80, '해외영업담당', 4700000, '2019-10-06', 'active', 'Singapore', 'employee1104@example.com'),
    (1105, '서예린', 10, 'BI개발자', 4300000, '2021-12-05', 'active', 'Germany', 'employee1105@example.com'),
    (1106, '임민준', 20, 'ML엔지니어', 4900000, '2023-03-28', 'active', 'United States', 'employee1106@example.com'),
    (1107, '송현우', 30, '고객상담원', 3800000, '2020-03-07', 'active', 'South Korea', 'employee1107@example.com'),
    (1108, '황하은', 40, '고객관리자', 5200000, '2022-01-27', 'active', 'South Korea', 'employee1108@example.com'),
    (1109, '한지훈', 50, '인사팀장', 6800000, '2023-04-21', 'active', 'South Korea', 'employee1109@example.com'),
    (1110, '안민서', 60, '시장분석가', 6000000, '2025-08-19', 'active', 'South Korea', 'employee1110@example.com'),
    (1111, '신민준', 70, '예산분석가', 5500000, '2021-05-02', 'active', 'Japan', 'employee1111@example.com'),
    (1112, '송하은', 80, '해외사업팀장', 7800000, '2018-11-13', 'active', 'United States', 'employee1112@example.com'),
    (1113, '송도윤', 10, '데이터엔지니어', 5000000, '2024-05-20', 'active', 'Germany', 'employee1113@example.com'),
    (1114, '한민준', 20, '연구팀장', 6000000, '2020-11-04', 'active', 'Singapore', 'employee1114@example.com'),
    (1115, '이유진', 30, '고객상담원', 4200000, '2020-06-22', 'active', 'South Korea', 'employee1115@example.com'),
    (1116, '박지민', 40, '영업담당자', 4400000, '2018-11-10', 'active', 'Japan', 'employee1116@example.com'),
    (1117, '장준호', 50, '교육담당자', 4900000, '2018-06-21', 'leave', 'South Korea', 'employee1117@example.com'),
    (1118, '권지민', 60, '콘텐츠기획자', 4600000, '2024-01-09', 'leave', 'South Korea', 'employee1118@example.com'),
    (1119, '이수빈', 70, '재무담당자', 3700000, '2018-04-20', 'active', 'South Korea', 'employee1119@example.com'),
    (1120, '이나연', NULL, '프로젝트지원담당', 4800000, '2023-05-21', 'active', 'Japan', 'employee1120@example.com'),
    (1121, '신지민', 10, '데이터분석가', 4000000, '2022-03-08', 'active', 'South Korea', 'employee1121@example.com'),
    (1122, '정예린', 20, 'AI연구원', 6500000, '2020-09-10', 'leave', 'Japan', 'employee1122@example.com'),
    (1123, '조수빈', 30, 'VOC분석가', 4400000, '2019-03-19', 'active', 'Japan', 'employee1123@example.com'),
    (1124, '한소윤', 40, '영업담당자', 5100000, '2020-06-06', 'active', 'Germany', 'employee1124@example.com'),
    (1125, '오태현', 50, '인사팀장', 7400000, '2018-11-26', 'active', 'South Korea', 'employee1125@example.com'),
    (1126, '이성민', 60, '마케팅담당자', 5200000, '2024-11-23', 'leave', 'South Korea', 'employee1126@example.com'),
    (1127, '정나연', 70, '회계담당자', 3500000, '2026-01-05', 'active', 'South Korea', 'employee1127@example.com'),
    (1128, '한유진', 80, '지역전략담당', 3700000, '2022-02-14', 'active', 'South Korea', 'employee1128@example.com'),
    (1129, '강다은', 10, '분석팀장', 6100000, '2024-01-13', 'active', 'South Korea', 'employee1129@example.com'),
    (1130, '윤지훈', 20, 'AI엔지니어', 6200000, '2018-12-26', 'active', 'South Korea', 'employee1130@example.com'),
    (1131, '최서연', 30, 'VOC분석가', 5300000, '2019-05-02', 'active', 'United States', 'employee1131@example.com'),
    (1132, '홍현우', 40, '영업담당자', 4300000, '2020-05-31', 'leave', 'Singapore', 'employee1132@example.com'),
    (1133, '황태현', 50, '인사팀장', 7200000, '2026-06-24', 'active', 'South Korea', 'employee1133@example.com'),
    (1134, '임나연', 60, '콘텐츠기획자', 4600000, '2021-11-23', 'active', 'Germany', 'employee1134@example.com'),
    (1135, '홍유진', 70, '재무팀장', 6800000, '2022-06-16', 'active', 'Singapore', 'employee1135@example.com'),
    (1136, '권우진', 80, '지역전략담당', 5000000, '2018-02-08', 'active', 'South Korea', 'employee1136@example.com'),
    (1137, '최채원', 10, 'BI개발자', 4500000, '2025-05-16', 'leave', 'United States', 'employee1137@example.com'),
    (1138, '안우진', 20, 'AI연구원', 4900000, '2023-08-13', 'leave', 'South Korea', 'employee1138@example.com'),
    (1139, '황채원', 30, 'VOC분석가', 5300000, '2026-03-14', 'active', 'Germany', 'employee1139@example.com'),
    (1140, '홍준호', NULL, '프로젝트지원담당', 3400000, '2023-03-31', 'active', 'United States', 'employee1140@example.com'),
    (1141, '김민서', 50, '인사팀장', 6300000, '2018-08-29', 'active', 'Singapore', 'employee1141@example.com'),
    (1142, '신준호', 60, '시장분석가', 5200000, '2021-03-02', 'retired', 'Japan', 'employee1142@example.com'),
    (1143, '김예린', 70, '재무담당자', 4600000, '2020-12-25', 'active', 'Singapore', 'employee1143@example.com'),
    (1144, '윤태현', 80, '해외영업담당', 4100000, '2018-08-27', 'active', 'South Korea', 'employee1144@example.com'),
    (1145, '권하은', 10, '분석팀장', 7000000, '2020-01-02', 'active', 'South Korea', 'employee1145@example.com'),
    (1146, '임우진', 20, '연구팀장', 6000000, '2019-07-12', 'active', 'South Korea', 'employee1146@example.com'),
    (1147, '권성민', 30, '고객상담원', 4100000, '2025-07-08', 'active', 'South Korea', 'employee1147@example.com'),
    (1148, '한민준', 40, '영업팀장', 6000000, '2026-05-09', 'active', 'South Korea', 'employee1148@example.com'),
    (1149, '장태현', 50, '교육담당자', 5200000, '2026-03-23', 'leave', 'South Korea', 'employee1149@example.com'),
    (1150, '윤다은', 60, '시장분석가', 5100000, '2020-07-24', 'active', 'Singapore', 'employee1150@example.com'),
    (1151, '오수빈', 70, '재무팀장', 6500000, '2020-02-06', 'active', 'Singapore', 'employee1151@example.com'),
    (1152, '최민준', 80, '해외사업팀장', 7200000, '2019-02-15', 'active', 'South Korea', 'employee1152@example.com'),
    (1153, '박다은', 10, 'BI개발자', 5600000, '2021-11-13', 'active', 'United States', 'employee1153@example.com'),
    (1154, '한승현', 20, 'AI연구원', 5500000, '2019-06-19', 'active', 'South Korea', 'employee1154@example.com'),
    (1155, '홍지민', 30, '고객상담원', 4100000, '2021-12-10', 'active', 'South Korea', 'employee1155@example.com'),
    (1156, '신우진', 40, '고객관리자', 5700000, '2021-09-12', 'active', 'South Korea', 'employee1156@example.com'),
    (1157, '이태현', 50, '인사팀장', 6200000, '2025-03-30', 'active', 'Singapore', 'employee1157@example.com'),
    (1158, '조민서', 60, '마케팅팀장', 6500000, '2025-02-18', 'active', 'South Korea', 'employee1158@example.com'),
    (1159, '한나연', 70, '예산분석가', 4700000, '2026-03-05', 'leave', 'South Korea', 'employee1159@example.com'),
    (1160, '조서연', NULL, '프로젝트지원담당', 4500000, '2026-01-17', 'active', 'South Korea', 'employee1160@example.com'),
    (1161, '한나연', 10, '데이터분석가', 5000000, '2019-05-22', 'active', 'Germany', 'employee1161@example.com'),
    (1162, '오승현', 20, 'ML엔지니어', 5800000, '2024-09-24', 'active', 'Germany', 'employee1162@example.com'),
    (1163, '송도윤', 30, '품질관리자', 4800000, '2022-02-17', 'active', 'South Korea', 'employee1163@example.com'),
    (1164, '김성민', 40, '영업팀장', 6800000, '2021-07-10', 'active', 'Singapore', 'employee1164@example.com'),
    (1165, '장준호', 50, '인사팀장', 6500000, '2023-04-24', 'active', 'South Korea', 'employee1165@example.com'),
    (1166, '한채원', 60, '마케팅담당자', 5000000, '2019-06-09', 'active', 'Japan', 'employee1166@example.com'),
    (1167, '장지민', 70, '예산분석가', 6000000, '2021-07-06', 'active', 'United States', 'employee1167@example.com'),
    (1168, '안소윤', 80, '해외영업담당', 4600000, '2019-10-26', 'leave', 'South Korea', 'employee1168@example.com'),
    (1169, '최민서', 10, '데이터분석가', 4100000, '2021-11-21', 'active', 'South Korea', 'employee1169@example.com'),
    (1170, '신우진', 20, '연구팀장', 7400000, '2026-06-15', 'active', 'Germany', 'employee1170@example.com'),
    (1171, '조다은', 30, '지원팀장', 7700000, '2018-01-08', 'active', 'South Korea', 'employee1171@example.com'),
    (1172, '조우진', 40, '영업팀장', 6000000, '2021-02-07', 'active', 'South Korea', 'employee1172@example.com'),
    (1173, '장다은', 50, '교육담당자', 4300000, '2018-09-21', 'active', 'United States', 'employee1173@example.com'),
    (1174, '장나연', 60, '마케팅팀장', 7300000, '2022-07-07', 'active', 'Japan', 'employee1174@example.com'),
    (1175, '정지민', 70, '예산분석가', 4400000, '2019-04-10', 'leave', 'Singapore', 'employee1175@example.com'),
    (1176, '안우진', 80, '해외영업담당', 3800000, '2025-06-14', 'active', 'South Korea', 'employee1176@example.com'),
    (1177, '장지민', 10, '데이터분석가', 3900000, '2019-06-12', 'active', 'Singapore', 'employee1177@example.com'),
    (1178, '김수빈', 20, '연구팀장', 7400000, '2021-09-19', 'active', 'South Korea', 'employee1178@example.com'),
    (1179, '전소윤', 30, '지원팀장', 7000000, '2018-04-17', 'active', 'Japan', 'employee1179@example.com'),
    (1180, '장다은', NULL, '프로젝트지원담당', 4100000, '2021-09-26', 'leave', 'Japan', 'employee1180@example.com'),
    (1181, '임지훈', 50, '인사담당자', 4000000, '2026-02-28', 'active', 'Singapore', 'employee1181@example.com'),
    (1182, '장지민', 60, '시장분석가', 5800000, '2022-02-17', 'active', 'South Korea', 'employee1182@example.com'),
    (1183, '홍승현', 70, '재무담당자', 4400000, '2018-04-08', 'active', 'Japan', 'employee1183@example.com'),
    (1184, '강서연', 80, '지역전략담당', 4100000, '2019-02-06', 'active', 'South Korea', 'employee1184@example.com'),
    (1185, '송우진', 10, 'BI개발자', 4200000, '2020-08-13', 'active', 'Germany', 'employee1185@example.com'),
    (1186, '이현우', 20, 'ML엔지니어', 5000000, '2025-11-22', 'active', 'Singapore', 'employee1186@example.com'),
    (1187, '한성민', 30, '지원팀장', 7200000, '2024-12-14', 'active', 'South Korea', 'employee1187@example.com'),
    (1188, '박준호', 40, '영업담당자', 3800000, '2022-05-14', 'active', 'Singapore', 'employee1188@example.com'),
    (1189, '박유진', 50, '교육담당자', 3700000, '2024-02-25', 'active', 'South Korea', 'employee1189@example.com'),
    (1190, '송우진', 60, '콘텐츠기획자', 4300000, '2022-09-18', 'active', 'United States', 'employee1190@example.com'),
    (1191, '윤하은', 70, '예산분석가', 5000000, '2022-11-01', 'active', 'Singapore', 'employee1191@example.com'),
    (1192, '정승현', 80, '해외사업팀장', 7100000, '2023-10-27', 'active', 'South Korea', 'employee1192@example.com'),
    (1193, '김유진', 10, 'BI개발자', 6100000, '2019-11-18', 'active', 'South Korea', 'employee1193@example.com'),
    (1194, '강민서', 20, 'AI엔지니어', 5700000, '2023-10-20', 'active', 'Japan', 'employee1194@example.com'),
    (1195, '임소윤', 30, '고객상담원', 3400000, '2026-05-27', 'active', 'South Korea', 'employee1195@example.com'),
    (1196, '한성민', 40, '영업담당자', 4100000, '2022-05-01', 'active', 'South Korea', 'employee1196@example.com'),
    (1197, '윤예린', 50, '채용담당자', 5200000, '2020-12-04', 'leave', 'South Korea', 'employee1197@example.com'),
    (1198, '윤민서', 60, '마케팅팀장', 7000000, '2026-01-31', 'active', 'South Korea', 'employee1198@example.com'),
    (1199, '이성민', 70, '재무팀장', 7600000, '2019-03-05', 'retired', 'South Korea', 'employee1199@example.com'),
    (1200, '정민서', NULL, '프로젝트지원담당', 3900000, '2018-04-10', 'active', 'Singapore', 'employee1200@example.com');

COMMIT;


/*
============================================================
데이터 입력 결과 확인
============================================================
*/

SELECT
    COUNT(*) AS department_count
FROM python_lab.department;

SELECT
    COUNT(*) AS employee_count
FROM python_lab.employee;

SELECT
    employment_status,
    COUNT(*) AS employee_count
FROM python_lab.employee
GROUP BY employment_status
ORDER BY employment_status;

SELECT
    employee_id,
    employee_name,
    department_id,
    job_title,
    salary,
    hire_date,
    employment_status,
    country_name,
    email
FROM python_lab.employee
ORDER BY employee_id
LIMIT 10;




-- 파이썬에서 실행할 코드

SELECT
	current_database() AS database_name,
	current_user AS login_user,
	current_schema() AS current_schema,
	version() AS postgresql_version

SELECT
	(SELECT COUNT(*)
	FROM python_lab.department) AS department_count,
	(SELECT COUNT(*)
	FROM python_lab.department) AS employee_count;



