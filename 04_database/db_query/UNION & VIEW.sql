-- UNION
SELECT 
	department_id AS reference_id,
	department_name AS reference_name,
	'부서' AS reference_type
FROM join_basic.department
UNION ALL
SELECT
	employee_id,
	employee_name,
	'직원'
FROM join_basic.employee;

-- 합집합(중복값 미포함)
SELECT 
	department_id 
FROM join_basic.employee
WHERE department_id IS NOT NULL
UNION
SELECT
	department_id
FROM join_basic.department;
	
-- union시 행단위 기준으로 판단.
SELECT
	'직원 소속 부서' AS source_type,
	department_id
FROM join_basic.employee
WHERE department_id IS NOT NULL
UNION
SELECT
	'부서 기준정보',
	department_id
FROM join_basic.department;



SELECT
	employee_id,
	employee_name
FROM join_basic.employee
WHERE salary >= 4000000
UNION
SELECT
	employee_id,
	employee_name
FROM join_basic.employee
WHERE department_id IN (10,20);


SELECT
	d.department_name AS category_name,
	COUNT(e.employee_id) AS employee_count
FROM join_basic.department AS d 
LEFT JOIN join_basic.employee AS e
	ON d.department_id = e.department_id
GROUP BY
	d.department_id,
	d.department_name
UNION ALL
SELECT 
	'전체 직원',
	COUNT(*)
FROM join_basic.employee;




-- VIEW( like 가상 테이블변수에 쿼리결과를 저장)
CREATE VIEW join_basic.vw_employee_basic AS
SELECT
	employee_id,
	employee_name,
	department_id,
	salary
FROM join_basic.employee;


SELECT * FROM join_basic.vw_employee_basic;



CREATE VIEW join_basic.vw_employee_department AS
SELECT
	e.employee_id,
	e.employee_name,
	e.salary,
	e.department_id,
	COALESCE(d.department_name, '부서 미배정') AS department_name
FROM join_basic.employee AS e
LEFT JOIN join_basic.department AS d
       ON e.department_id = d.department_id;




SELECT * FROM join_basic.vw_employee_department;

SELECT
	employee_id,
	employee_name,
	department_name,
	salary
FROM join_basic.vw_employee_department
WHERE department_name = '데이터팀'
ORDER BY employee_id;


CREATE OR REPLACE VIEW join_basic.vw_employee_basic AS
SELECT
	employee_id,
	employee_name,
	department_id,
	salary,
	CASE
		WHEN salary >= 4500000 THEN 'HIGH'
		WHEN salary >= 4000000 THEN 'MIDDLE'
		ELSE 'BASIC'
	END AS salary_grade
FROM join_basic.employee;

SELECT * FROM join_basic.vw_employee_basic;


DROP VIEW join_basic.vw_employee_basic;
DROP VIEW join_basic.vw_employee_department;

