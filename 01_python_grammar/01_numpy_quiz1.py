import numpy as np

scores = np.array([
    [98, 70, 99],
    [60, 55, 65],
    [92, 88, 95],
    [75, 80, 78],
    [50, 45, 60]
])

bonus = np.array([5, 0, 3])

# --------------------------------------------------
# 1. 원본 성적과 배열 모양
# --------------------------------------------------
print("원본 성적")
print(scores)

print("\n배열의 모양")
print(scores.shape)

# --------------------------------------------------
# 2. 브로드캐스팅으로 과목별 추가 점수 적용
# --------------------------------------------------
bonus_scores = scores + bonus

print("\n추가 점수 적용 결과")
print(bonus_scores)

# --------------------------------------------------
# 3. 100점을 초과하는 점수는 100으로 제한
# --------------------------------------------------
final_scores = np.where(
    bonus_scores > 100,
    100,
    bonus_scores
)

print("\n최종 성적")
print(final_scores)

# --------------------------------------------------
# 4. 각 학생의 총점
# axis=1: 각 행을 기준으로 계산
# --------------------------------------------------
student_totals = final_scores.sum(axis=1)

print("\n학생별 총점")
print(student_totals)

# --------------------------------------------------
# 5. 각 학생의 평균
# --------------------------------------------------
student_averages = final_scores.mean(axis=1)

print("\n학생별 평균")
print(student_averages)

# --------------------------------------------------
# 6. 각 과목의 평균
# axis=0: 각 열을 기준으로 계산
# --------------------------------------------------
subject_averages = final_scores.mean(axis=0)

print("\n과목별 평균")
print(subject_averages)

# --------------------------------------------------
# 7. 한 과목이라도 95점 이상인 학생
# --------------------------------------------------
high_score_student_mask = (final_scores >= 95).any(axis=1)

print("\n한 과목이라도 95점 이상인지 확인")
print(high_score_student_mask)

print("\n한 과목이라도 95점 이상인 학생의 성적")
print(final_scores[high_score_student_mask])

# --------------------------------------------------
# 8. 한 학생이라도 100점을 받은 과목
# --------------------------------------------------
perfect_subject_mask = (final_scores == 100).any(axis=0)

print("\n100점을 받은 학생이 있는 과목인지 확인")
print(perfect_subject_mask)

print("\n한 학생이라도 100점을 받은 과목")
print(final_scores[:, perfect_subject_mask])

# --------------------------------------------------
# 9. 학생별 점수를 오름차순 정렬
# --------------------------------------------------
sorted_scores = np.sort(final_scores, axis=1)

print("\n학생별 점수 오름차순 정렬")
print(sorted_scores)

# --------------------------------------------------
# 10. 60점 미만의 값만 선택
# --------------------------------------------------
low_scores = final_scores[final_scores < 60]

print("\n60점 미만의 점수")
print(low_scores)