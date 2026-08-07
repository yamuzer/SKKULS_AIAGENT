import numpy as np
import pandas as pd


# ============================================================
# 1. 고객 정보와 상품 정보 파일 읽기
# ============================================================
customers = pd.read_json(
    "./data/customer_master.json",
    encoding="utf-8"
)

products = pd.read_excel(
    "./data/product_master.xlsx",
    sheet_name="상품"
)

print("고객 정보")
print(customers)
print()

print("상품 정보")
print(products)
print()


# ============================================================
# 2. 주문 데이터를 chunk 단위로 읽고 연결
# ============================================================
chunker = pd.read_csv(
    "./data/orders.csv",
    encoding="utf-8-sig",
    chunksize=7
)

order_chunks = []

for chunk_number, chunk in enumerate(chunker, start=1):
    print(f"{chunk_number}번째 주문 데이터 조각")
    print(chunk)
    print()

    order_chunks.append(chunk)

orders = pd.concat(
    order_chunks,
    ignore_index=True
)

print("통합 주문 데이터")
print(orders)
print()


# ============================================================
# 3. 주문, 고객, 상품 데이터 병합
# ============================================================
merged = pd.merge(
    orders,
    customers,
    on="고객번호",
    how="left"
)

merged = pd.merge(
    merged,
    products,
    on="상품번호",
    how="left"
)

print("통합 분석 데이터")
print(merged)
print()


# ============================================================
# 4. 주문금액 계산
# ============================================================
merged["주문금액"] = merged["수량"] * merged["단가"]

print("주문금액 계산 결과")
print(
    merged[
        ["주문번호", "고객명", "상품명", "수량", "단가", "주문금액"]
    ]
)
print()


# ============================================================
# 5. 연령대 구분
# ============================================================
age_bins = [20, 30, 40, 50, 100]
age_labels = ["20대", "30대", "40대", "50대 이상"]

merged["연령대"] = pd.cut(
    merged["나이"],
    bins=age_bins,
    labels=age_labels,
    right=False
)

print("연령대 구분 결과")
print(
    merged[
        ["고객번호", "고객명", "나이", "연령대"]
    ].drop_duplicates()
)
print()


# ============================================================
# 6. 고객별 구매 실적 계산
# ============================================================
customer_summary = (
    merged
    .groupby(
        ["고객번호", "고객명", "지역"],
        as_index=False
    )
    .agg(
        주문금액합계=("주문금액", "sum"),
        평균주문금액=("주문금액", "mean"),
        주문건수=("주문번호", "count"),
        총구매수량=("수량", "sum")
    )
)

print("고객별 구매 실적")
print(customer_summary)
print()


# ============================================================
# 7. 고객 등급 지정
# ============================================================
grade_bins = [0, 700000, 1300000, np.inf]
grade_labels = ["일반", "우수", "VIP"]

customer_summary["고객등급"] = pd.cut(
    customer_summary["주문금액합계"],
    bins=grade_bins,
    labels=grade_labels,
    right=False
)

print("고객 등급 지정 결과")
print(customer_summary)
print()


# ============================================================
# 8. VIP 고객 조회
# ============================================================
vip_customers = customer_summary[
    customer_summary["고객등급"] == "VIP"
]

print("VIP 고객")
print(
    vip_customers[
        ["고객명", "지역", "주문금액합계", "주문건수"]
    ]
)
print()


# ============================================================
# 9. 상품분류별 판매 실적
# ============================================================
category_summary = (
    merged
    .groupby("상품분류")
    .agg(
        주문금액합계=("주문금액", "sum"),
        평균주문금액=("주문금액", "mean"),
        최대주문금액=("주문금액", "max"),
        판매수량합계=("수량", "sum"),
        주문건수=("주문번호", "count")
    )
    .sort_values(
        by="주문금액합계",
        ascending=False
    )
)

print("상품분류별 판매 실적")
print(category_summary)
print()


# ============================================================
# 10. 연령대와 상품분류별 구매 분석
# ============================================================
age_category_summary = (
    merged
    .groupby(
        ["연령대", "상품분류"],
        observed=True
    )
    .agg(
        주문금액합계=("주문금액", "sum"),
        평균주문금액=("주문금액", "mean")
    )
)

print("연령대와 상품분류별 구매 분석")
print(age_category_summary)
print()


# ============================================================
# 11. 상품분류별 주문금액 상위 2개
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
        [
            "상품분류",
            "주문번호",
            "고객명",
            "상품명",
            "주문월",
            "주문금액"
        ]
    ]
)
print()


# ============================================================
# 12. 상품분류별 월별 매출표
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
    columns=["1월", "2월", "3월"],
    fill_value=0
)

print("상품분류별 월별 매출표")
print(monthly_sales)
print()


# ============================================================
# 13. 월별 매출표를 긴 형태로 변환
# ============================================================
long_monthly_sales = (
    monthly_sales
    .stack()
    .reset_index(name="매출액")
)

print("긴 형태의 월별 매출 데이터")
print(long_monthly_sales)
print()


# ============================================================
# 14. 주문금액 상위 5건
# ============================================================
top_five_orders = (
    merged
    .sort_values(
        by="주문금액",
        ascending=False
    )
    .head(5)
)

print("주문금액 상위 5건")
print(
    top_five_orders[
        [
            "주문번호",
            "고객명",
            "지역",
            "상품명",
            "상품분류",
            "수량",
            "주문금액"
        ]
    ]
)
print()


# ============================================================
# 15. 고객별 분석 결과 저장
# ============================================================
customer_summary.to_csv(
    "./data/customer_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("저장 완료: ./data/customer_summary.csv")
