print(
'''
1.문제  학생 성적 분석
다섯 학생의 세 과목 점수가 다음과 같이 주어졌습니다.
'''
)
import numpy as np
scores = np.array([
    [98, 70, 99],
    [60, 55, 65],
    [92, 88, 95],
    [75, 80, 78],
    [50, 45, 60]
])
# 과목별 추가 점수는 다음과 같습니다.
bonus = np.array([5, 0, 3])
# 다음 작업을 순서대로 수행하세요.
#
print('1) 원본 성적 배열과 배열의 모양 출력')
print(scores.shape)
print(scores)

print('2) 브로드캐스팅을 이용하여 과목별 추가 점수 적용')
add_scores = [1, 2, 3]
new_scores = scores + add_scores
print(new_scores)

print('3) 추가 점수를 적용한 결과가 100을 초과하면 100으로 변경')
new_scores1 = np.where(new_scores > 100, 100, new_scores)
print(new_scores1)

print('4) 각 학생의 총점 계산')
print(new_scores1.sum(axis=1))

print('5) 각 학생의 평균 계산')
print(new_scores1.mean(axis=1))

print('6) 각 과목의 평균 계산')
print(new_scores1.mean(axis=0))

print('7) 한 과목이라도 95점 이상인 학생 찾기')
print(new_scores1 >= 95)
print(np.any(new_scores1 >= 95, axis=1))
print((new_scores1 >= 95).any(axis=1))

print('8) 한 학생이라도 100점을 받은 과목 찾기')
print(new_scores1)
print(np.any(new_scores1 == 100, axis=0))

print('9) 학생별 성적을 오름차순으로 정렬')
print(new_scores1)
new_scores1.sort(axis=1)
print(new_scores1)

print('10) 모든 점수 중 60점 미만인 값만 출력')
print(new_scores1[new_scores1 < 60])


print('='*100)

print(
'''
2.  실습 문제: 학생 성적 관리
여러 학생의 이름과 국어, 영어, 수학 점수를 반복해서 입력받아 성적을 분석하는 프로그램을 작성하세요.
[실행 조건]
* 학생 이름은 중복되지 않는다고 가정합니다.
* 점수는 `국어 영어 수학` 순서로 입력합니다.
* 점수는 공백으로 구분된 정수 3개를 입력합니다.
* NumPy의 `array`, `sum`, `mean`, `std`, `var`와 불리언 인덱싱을 사용합니다.
[요구사항]
''')
print('1. 학생의 이름과 국어, 영어, 수학 점수를 입력받습니다.')
students_names = np.array([])
students_scores = np.array([])
for i in range(3):
    student_name = input('이름을 입력하세요.')
    korean_score, english_score, math_score = input('국어, 영어, 수학 점수를 순서대로 공백으로 구분하여 입력하세요.').split()
    np.append(students_names, student_name)
    np.append(students_scores, [korean_score, english_score, math_score])
print(students_names, students_scores)



print('2. 입력한 이름은 리스트에, 점수는 2차원 리스트에 저장합니다.')


print('3. 계속 입력할 것인지 `y/n`으로 확인하며, `n`을 입력하면 입력을 종료합니다.')


print('4. 점수 데이터를 NumPy 배열로 변환한 뒤 전체 성적을 출력합니다.')


print('5. `axis=0`을 이용하여 국어, 영어, 수학의 과목별 총점을 출력합니다.')


print('6. 성적을 조회할 학생의 이름을 입력받습니다.')


print('7. 이름 배열과 불리언 인덱싱을 이용하여 해당 학생의 점수를 찾습니다.')


print('8. 조회한 학생의 과목 점수, 평균, 표준편차, 분산을 출력합니다.')


print('9. 입력한 이름의 학생이 없으면 `해당 학생을 찾을 수 없습니다.`를 출력합니다.')

