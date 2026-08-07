import pandas as pd


# ============================================================
# 1. 파일에서 데이터 불러오기
# ============================================================
customers = pd.read_json(
    "./data/customers.json",
    encoding="utf-8"
)

orders_jan = pd.read_csv(
    "./data/orders_jan.csv",
    encoding="utf-8-sig"
)

orders_feb = pd.read_csv(
    "./data/orders_feb.csv",
    encoding="utf-8-sig"
)

print("고객 데이터")
print(customers)
print()

print("1월 주문 데이터")
print(orders_jan)
print()

print("2월 주문 데이터")
print(orders_feb)
print()


# ============================================================
# 2. 주문월 열 추가
# ============================================================
orders_jan["주문월"] = "1월"
orders_feb["주문월"] = "2월"


# ============================================================
# 3. 1월과 2월 주문 데이터 연결
# ============================================================
orders = pd.concat(
    [orders_jan, orders_feb],
    ignore_index=True
)

print("통합 주문 데이터")
print(orders)
print()


# ============================================================
# 4. 주문 데이터와 고객 데이터 병합
# ============================================================
merged = pd.merge(
    orders,
    customers,
    on="고객번호",
    how="left"
)

print("고객 정보가 결합된 주문 데이터")
print(merged)
print()


# ============================================================
# 5. 주문금액 계산
# ============================================================
merged["주문금액"] = merged["수량"] * merged["단가"]

print("주문금액 추가 결과")
print(merged)
print()


# ============================================================
# 6. 연령대 구분
# ============================================================
age_bins = [20, 30, 40, 50, 100]
age_labels = ["20대", "30대", "40대", "50대 이상"]

merged["연령대"] = pd.cut(
    merged["나이"],
    bins=age_bins,
    labels=age_labels,
    right=False
)

print("연령대 추가 결과")
print(merged[["고객명", "나이", "연령대"]].drop_duplicates())
print()


# ============================================================
# 7. 지역별 주문 분석
# ============================================================
region_result = merged.groupby("지역").agg(
    주문금액합계=("주문금액", "sum"),
    주문금액평균=("주문금액", "mean"),
    주문건수=("주문번호", "count")
)

print("지역별 주문 분석")
print(region_result)
print()


# ============================================================
# 8. 상품분류별 주문 분석
# ============================================================
category_result = merged.groupby("상품분류").agg(
    주문금액합계=("주문금액", "sum"),
    주문금액평균=("주문금액", "mean"),
    최대주문금액=("주문금액", "max"),
    판매수량합계=("수량", "sum")
)

print("상품분류별 주문 분석")
print(category_result)
print()


# ============================================================
# 9. 연령대와 상품분류별 평균 주문금액
# ============================================================
age_category_result = (
    merged
    .groupby(
        ["연령대", "상품분류"],
        observed=True
    )["주문금액"]
    .mean()
)

print("연령대와 상품분류별 평균 주문금액")
print(age_category_result)
print()


# ============================================================
# 10. 상품분류별 주문금액 상위 2개
# ============================================================
def get_top_orders(group_data, n=2):
    result = (
        group_data
        .sort_values(
            by="주문금액",
            ascending=False
        )
        .head(n)
        .copy()
    )

    # pandas 3.0에서는 apply 함수에 그룹 기준 열이 전달되지 않는다.
    # group_data.name에 저장된 그룹 이름으로 상품분류 열을 복원한다.
    result.insert(0, "상품분류", group_data.name)

    return result


top_orders = (
    merged
    .groupby(
        "상품분류",
        group_keys=False
    )
    .apply(
        get_top_orders,
        n=2,
        include_groups=False
    )
    .reset_index(drop=True)
)

print("상품분류별 주문금액 상위 2개")
print(
    top_orders[
        ["상품분류", "주문번호", "고객명", "주문월", "주문금액"]
    ]
)
print()


# ============================================================
# 11. 상품분류별 월별 매출표
# ============================================================
monthly_sales = (
    merged
    .groupby(
        ["상품분류", "주문월"]
    )["주문금액"]
    .sum()
    .unstack(fill_value=0)
)

monthly_sales = monthly_sales.reindex(
    columns=["1월", "2월"],
    fill_value=0
)

print("상품분류별 월별 매출표")
print(monthly_sales)
print()


# ============================================================
# 12. 월별 매출표를 긴 형태로 변환
# ============================================================
long_sales = (
    monthly_sales
    .stack()
    .reset_index(name="매출액")
)

print("긴 형태의 월별 매출 데이터")
print(long_sales)
print()


# ============================================================
# 13. 주문금액 내림차순 정렬
# ============================================================
sorted_orders = merged.sort_values(
    by="주문금액",
    ascending=False
)

print("주문금액 내림차순 정렬")
print(
    sorted_orders[
        [
            "주문번호",
            "고객명",
            "지역",
            "연령대",
            "상품분류",
            "주문월",
            "주문금액"
        ]
    ]
)
