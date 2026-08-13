import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# 1. Self-Attention 클래스
# ============================================================

class SimpleSelfAttention(nn.Module):

    def __init__(
        self,
        embedding_dim,
    ):
        super().__init__()

        # 입력 벡터를 Query로 변환하는 Linear
        self.query = nn.Linear(
            embedding_dim,
            embedding_dim,
            bias=False,
        )

        # 입력 벡터를 Key로 변환하는 Linear
        self.key = nn.Linear(
            embedding_dim,
            embedding_dim,
            bias=False,
        )

        # 입력 벡터를 Value로 변환하는 Linear
        self.value = nn.Linear(
            embedding_dim,
            embedding_dim,
            bias=False,
        )


    def forward(
        self,
        x,
    ):

        # ----------------------------------------------------
        # 1. 입력 X로부터 Q, K, V 생성
        # ----------------------------------------------------

        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)


        # ----------------------------------------------------
        # 2. Q와 K의 유사도 계산
        # ----------------------------------------------------

        attention_score = (
            Q @ K.T
        )


        # ----------------------------------------------------
        # 3. Scaling
        # ----------------------------------------------------

        d_k = Q.shape[-1]

        scaled_score = (
            attention_score
            / (d_k ** 0.5)
        )


        # ----------------------------------------------------
        # 4. Softmax
        # ----------------------------------------------------

        attention_weights = F.softmax(
            scaled_score,
            dim=-1,
        )


        # ----------------------------------------------------
        # 5. Value 결합
        # ----------------------------------------------------

        output = (
            attention_weights @ V
        )


        return (
            output,
            attention_weights,
            Q,
            K,
            V,
        )


# ============================================================
# 2. 입력 데이터
# ============================================================

words = [
    "나는",
    "사과를",
    "먹는다",
]


X = torch.tensor(
    [
        [1.0, 0.0, 1.0, 0.0],   # 나는
        [0.0, 2.0, 0.0, 2.0],   # 사과를
        [1.0, 1.0, 1.0, 1.0],   # 먹는다
    ],
    dtype=torch.float32,
)


print("=" * 60)
print("입력 X")
print("=" * 60)

print(X)

print(
    "\nX shape:",
    X.shape,
)


# ============================================================
# 3. 모델 생성
# ============================================================

torch.manual_seed(42)

embedding_dim = X.shape[-1]

attention = SimpleSelfAttention(
    embedding_dim=embedding_dim,
)


# ============================================================
# 4. Self-Attention 실행
# ============================================================

(
    output,
    attention_weights,
    Q,
    K,
    V,
) = attention(X)


# ============================================================
# 5. Q 확인
# ============================================================

print("\n" + "=" * 60)
print("Query")
print("=" * 60)

print(Q)


# ============================================================
# 6. K 확인
# ============================================================

print("\n" + "=" * 60)
print("Key")
print("=" * 60)

print(K)


# ============================================================
# 7. V 확인
# ============================================================

print("\n" + "=" * 60)
print("Value")
print("=" * 60)

print(V)


# ============================================================
# 8. Attention Weight 확인
# ============================================================

print("\n" + "=" * 60)
print("Attention Weights")
print("=" * 60)

print(attention_weights)


# ============================================================
# 9. Attention Weight 행의 합 확인
# ============================================================

print("\n각 행의 합")

print(
    attention_weights.sum(
        dim=-1,
    )
)


# ============================================================
# 10. 최종 결과
# ============================================================

print("\n" + "=" * 60)
print("Self-Attention Output")
print("=" * 60)

print(output)

print(
    "\nOutput shape:",
    output.shape,
)


# ============================================================
# 11. 단어별 Attention 확인
# ============================================================

print("\n" + "=" * 60)
print("단어별 Attention")
print("=" * 60)


for i, query_word in enumerate(words):

    print(
        f"\n[{query_word}]가 참고하는 단어"
    )

    for j, key_word in enumerate(words):

        weight = attention_weights[
            i,
            j,
        ].item()

        print(
            f"{key_word:6s} : "
            f"{weight:.4f}"
        )