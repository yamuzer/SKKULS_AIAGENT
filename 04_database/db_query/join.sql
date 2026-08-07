-- INNER JOIN
SELECT
	e.employee_id,
	e.employee_name,
	d.department_name
FROM join_basic.employee AS e
INNER JOIN join_basic.department AS d
	ON e.department_id = d.department_id
ORDER BY e.employee_id;
	

-- LEFT JOIN
SELECT
	e.department_id,
	e.employee_name,
	e.department_id,
	d.department_name
FROM join_basic.employee AS e
LEFT JOIN join_basic.department AS d
	ON e.department_id = d.department_id
ORDER BY e.employee_id;

SELECT
	e.department_id,
	e.employee_name,
	e.department_id,
	d.department_name
FROM join_basic.department AS d
LEFT JOIN join_basic.employee AS e
	ON d.department_id = e.department_id
ORDER BY d.department_id, e.employee_id;


-- RIGHT JOIN
SELECT
	e.department_id,
	e.employee_name,
	d.department_name
FROM join_basic.department AS d
RIGHT JOIN join_basic.employee AS e
	ON d.department_id = e.department_id
ORDER BY e.employee_id;


-- FULL OUTER JOIN
SELECT
	e.department_id,
	e.employee_name,
	e.department_id,
	d.department_name
FROM join_basic.department AS d
FULL OUTER JOIN join_basic.employee AS e
	ON d.department_id = e.department_id
ORDER BY d.department_id NULLS LAST, e.employee_id NULLS LAST;


-- CLOSS JOIN
SELECT
	d.department_name,
	s.shift_name
FROM join_basic.department AS d
CROSS JOIN join_basic.work_shift AS s


--

SELECT
	e.employee_id,
	e.employee_name,
	COALESCE(d.department_name, '부서 미배정') AS department_name
FROM join_basic.employee AS e
LEFT JOIN join_basic.department AS d
	ON e.department_id = d.department_id


-- 부서에 연결되지 않은 직원 찾기
SELECT
	e.employee_id,
	e.employee_name,
	d.department_name
FROM join_basic.department AS d
LEFT JOIN join_basic.employee AS e
	ON e.department_id = d.department_id
WHERE e.employee_name is NULL;


-- LEFT JOIN 후 부서별 직원 수
SELECT
	d.department_id,
	d.department_name,
	COUNT(e.employee_id) as employee_count
FROM join_basic.department AS d
LEFT JOIN join_basic.employee AS e
	ON e.department_id = d.department_id
GROUP BY 
	d.department_id,
	d.department_name
ORDER BY d.department_id;


-- 직원이 없는 부서
SELECT
	e.employee_id,
	e.employee_name,
	d.department_name
FROM join_basic.employee AS e
LEFT JOIN join_basic.department AS d
	ON e.department_id = d.department_id
WHERE e.employee_name is NULL;



-- -----------------------------------------------------------
-- 문제 1. INNER JOIN
-- -----------------------------------------------------------
-- 부서가 배정된 직원만 조회하세요.
--
-- 출력 열:
-- employee_id, employee_name, department_name
--
-- employee_id 오름차순으로 정렬하세요.
SELECT  employee_id, employee_name, department_name
FROM join_basic.employee AS e
LEFT JOIN join_basic.department AS d
	ON e.department_id = d.department_id
WHERE e.department_id IS NOT NULL
ORDER BY employee_id ;


-- -----------------------------------------------------------
-- 문제 2. LEFT JOIN
-- -----------------------------------------------------------
-- 부서 배정 여부와 관계없이 모든 직원을 조회하세요.
--
-- 출력 열:
-- employee_id, employee_name, department_name
--
-- 부서가 없으면 '부서 미배정'으로 표시하세요.
-- employee_id 오름차순으로 정렬하세요.

SELECT  
	employee_id,
	employee_name, 
	COALESCE(d.department_name, '부서 미배정') AS department_name
FROM join_basic.employee AS e
LEFT JOIN join_basic.department AS d
	ON e.department_id = d.department_id
ORDER BY employee_id ;


-- -----------------------------------------------------------
-- 문제 3. 직원이 없는 부서 찾기
-- -----------------------------------------------------------
-- 모든 부서를 기준으로 직원 정보를 연결한 뒤,
-- 직원이 한 명도 없는 부서만 조회하세요.
--
-- 출력 열:
-- department_id, department_name

SELECT
	d.department_id, 
	d.department_name
FROM join_basic.department AS d
LEFT JOIN join_basic.employee AS e
	ON e.department_id = d.department_id
WHERE e.employee_id is NULL;


-- -----------------------------------------------------------
-- 문제 4. FULL OUTER JOIN
-- -----------------------------------------------------------
-- 모든 직원과 모든 부서를 조회하세요.
--
-- 다음 데이터가 모두 포함되어야 합니다.
-- 1. 부서가 있는 직원
-- 2. 부서가 없는 직원
-- 3. 직원이 없는 부서
--
-- 출력 열:
-- employee_id, employee_name,
-- department_id, department_name
SELECT
	e.department_id,
	e.employee_name,
	e.department_id,
	d.department_name
FROM join_basic.department AS d
FULL OUTER JOIN join_basic.employee AS e
	ON d.department_id = e.department_id
ORDER BY d.department_id, e.employee_id;


-- -----------------------------------------------------------
-- 문제 5. CROSS JOIN
-- -----------------------------------------------------------
-- 모든 부서와 모든 근무조의 조합을 조회하세요.
--
-- 출력 열:
-- department_name, shift_name


SELECT
	d.department_name,
	s.shift_name
FROM join_basic.department AS d
CROSS JOIN join_basic.work_shift AS s



-- -----------------------------------------------------------
-- 문제 6. 부서별 직원 수
-- -----------------------------------------------------------
-- 직원이 없는 부서까지 포함하여
-- 부서별 직원 수를 계산하세요.
--
-- 출력 열:
-- department_id, department_name, employee_count
--
-- 인사팀은 반드시 0명으로 표시되어야 합니다.
SELECT
	d.department_id,
	d.department_name,
	COUNT(e.employee_id) as employee_count
FROM join_basic.department AS d
LEFT JOIN join_basic.employee AS e
	ON e.department_id = d.department_id
GROUP BY 
	d.department_id,
	d.department_name
ORDER BY d.department_id;


