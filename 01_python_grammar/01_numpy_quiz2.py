import numpy as np


names = []
score_data = []


# ------------------------------------------------------------
# 1. 학생 이름과 성적 입력
# ------------------------------------------------------------
while True:
    name = input("이름을 입력하세요: ").strip()

    score_text = input(
        "국어 영어 수학 점수를 입력하세요: "
    )

    scores = list(map(int, score_text.split()))

    # 점수를 정확히 3개 입력했는지 확인
    if len(scores) != 3:
        print("국어, 영어, 수학 점수를 정확히 3개 입력하세요.")
        print()
        continue

    names.append(name)
    score_data.append(scores)

    continue_input = input(
        "입력을 계속 진행하시겠습니까? (y/n): "
    ).lower()

    if continue_input != "y":
        break


# ------------------------------------------------------------
# 2. 리스트를 NumPy 배열로 변환
# ------------------------------------------------------------
arr_names = np.array(names)
arr_scores = np.array(score_data)


print("\n전체 성적")
print(arr_scores)


# ------------------------------------------------------------
# 3. 과목별 총점 계산
# ------------------------------------------------------------
subject_totals = arr_scores.sum(axis=0)

print()
print(
    f"국어 총점: {subject_totals[0]}, "
    f"영어 총점: {subject_totals[1]}, "
    f"수학 총점: {subject_totals[2]}"
)


# ------------------------------------------------------------
# 4. 이름을 이용하여 학생 성적 검색
# ------------------------------------------------------------
print()

output_name = input(
    "성적을 출력할 학생의 이름을 입력하세요: "
).strip()

student_mask = arr_names == output_name
selected_scores = arr_scores[student_mask]


# ------------------------------------------------------------
# 5. 검색 결과 출력
# ------------------------------------------------------------
if selected_scores.size == 0:
    print(f"{output_name} 학생을 찾을 수 없습니다.")

else:
    # 이름은 중복되지 않는다는 조건으로 첫 번째 행 사용
    student_scores = selected_scores[0]

    print()
    print(f"{output_name} 과목 점수: {student_scores}")
    print(f"평균: {student_scores.mean():.2f}")
    print(f"표준편차: {student_scores.std():.2f}")
    print(f"분산: {student_scores.var():.2f}")