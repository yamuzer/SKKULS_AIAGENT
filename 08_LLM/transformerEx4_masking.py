import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# 1. Masked Self-Attention 클래스
# ============================================================

class MaskedSelfAttention(nn.Module):

    def __init__(
        self,
        embedding_dim,
    ):
        super().__init__()

        # Query 생성
        self.query = nn.Linear(
            embedding_dim,
            embedding_dim,
            bias=False,
        )

        # Key 생성
        self.key = nn.Linear(
            embedding_dim,
            embedding_dim,
            bias=False,
        )

        # Value 생성
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
        # 1. Q, K, V 생성
        # ----------------------------------------------------

        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)


        # ----------------------------------------------------
        # 2. Key의 마지막 두 차원 교환
        # ----------------------------------------------------

        K_T = K.transpose(
            -2,
            -1,
        )


        # ----------------------------------------------------
        # 3. Attention Score 계산
        # ----------------------------------------------------

        attention_score = (
            Q @ K_T
        )


        # ----------------------------------------------------
        # 4. Scaling
        # ----------------------------------------------------

        d_k = Q.shape[-1]

        scaled_score = (
            attention_score
            / (d_k ** 0.5)
        )

        # ----------------------------------------------------
        # 5. Causal Mask 생성
        # ----------------------------------------------------

        sequence_length = x.shape[1]

        mask = torch.tril(
            torch.ones(
                sequence_length,
                sequence_length,
                device=x.device
            )
        )
        print('\nmask:')
        print(mask)

        '''
        [[1, 0, 0],
         [1, 1, 0],
         [1, 1, 1]]
        '''

        # ----------------------------------------------------
        # 6. Mask 적용
        # ----------------------------------------------------

        masked_score = scaled_score.masked_fill(
            mask==0,
            float('-inf')  # e^-무한대 어텐션에서 행렬 계산이 안되도록 음수로 변경(NLP 입력 패딩마스크는 임베딩에서 계산안되도록 0으로 변경)
        )
        print('\nmasked score')
        print(masked_score)

        # ----------------------------------------------------
        # 7. Softmax
        # ----------------------------------------------------

        attention_weights = F.softmax(
            masked_score,
            dim=-1,
        )


        # ----------------------------------------------------
        # 6. Value와 결합
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

sentences = [
    [
        "나는",
        "사과를",
        "먹는다",
    ],
    [
        "나는",
        "학교에",
        "간다",
    ],
]


# ------------------------------------------------------------
# 문장 1
# ------------------------------------------------------------

sentence1 = [
    [1.0, 0.0, 1.0, 0.0],   # 나는
    [0.0, 2.0, 0.0, 2.0],   # 사과를
    [1.0, 1.0, 1.0, 1.0],   # 먹는다
]


# ------------------------------------------------------------
# 문장 2
# ------------------------------------------------------------

sentence2 = [
    [1.0, 0.0, 1.0, 0.0],   # 나는
    [2.0, 1.0, 0.0, 1.0],   # 학교에
    [1.0, 2.0, 1.0, 0.0],   # 간다
]


# ------------------------------------------------------------
# Tensor로 변환
# ------------------------------------------------------------

X = torch.tensor(
    [
        sentence1,
        sentence2,
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

model = MaskedSelfAttention(
    embedding_dim=embedding_dim,
)


# ============================================================
# 4. Attention 실행
# ============================================================

(
    output,
    attention_weights,
    Q,
    K,
    V,
) = model(X)


# ============================================================
# 5. Q 확인
# ============================================================

print("\n" + "=" * 60)
print("Q")
print("=" * 60)

print(Q)

print(
    "\nQ shape:",
    Q.shape,
)


# ============================================================
# 6. K 확인
# ============================================================

print("\n" + "=" * 60)
print("K")
print("=" * 60)

print(K)

print(
    "\nK shape:",
    K.shape,
)


# ============================================================
# 7. K transpose 확인
# ============================================================

K_T = K.transpose(
    -2,
    -1,
)

print("\n" + "=" * 60)
print("K transpose")
print("=" * 60)

print(K_T)

print(
    "\nK_T shape:",
    K_T.shape,
)


# ============================================================
# 8. Attention Weight 확인
# ============================================================

print("\n" + "=" * 60)
print("Attention Weights")
print("=" * 60)

print(attention_weights)

print(
    "\nAttention Weights shape:",
    attention_weights.shape,
)


# ============================================================
# 9. 각 행의 합 확인
# ============================================================

print("\n" + "=" * 60)
print("Attention Weight 행의 합")
print("=" * 60)

print(
    attention_weights.sum(
        dim=-1,
    )
)


# ============================================================
# 10. 최종 결과
# ============================================================

print("\n" + "=" * 60)
print("Attention Output")
print("=" * 60)

print(output)

print(
    "\nOutput shape:",
    output.shape,
)


# ============================================================
# 11. 문장별 Attention Weight 확인
# ============================================================

print("\n" + "=" * 60)
print("문장별 Attention 분석")
print("=" * 60)


for batch_index, words in enumerate(sentences):

    print()
    print(
        f"문장 {batch_index + 1}: "
        + " ".join(words)
    )

    for query_index, query_word in enumerate(words):

        print(
            f"\n[{query_word}]가 참고하는 정도"
        )

        for key_index, key_word in enumerate(words):

            weight = attention_weights[
                batch_index,
                query_index,
                key_index,
            ].item()

            print(
                f"{key_word:6s} : "
                f"{weight:.4f}"
            )