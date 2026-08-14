import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# 1. Multi-Head-Attention 클래스
# ============================================================

class SimpleMultiHeadAttention(nn.Module):

    def __init__(
        self,
        embedding_dim,
        num_heads
    ):
        super().__init__()

        assert embedding_dim % num_heads == 0
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads

        # 하나의 head가 담당하는 차원
        self.head_dim = embedding_dim // num_heads


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

        # 여러 head 의 경과를 다시 합친 후 적용할 linear
        self.output_linear = nn.Linear(
            embedding_dim,
            embedding_dim,
            bias=False
        )

        
    def forward(
        self,
        x,
    ):

        # ----------------------------------------------------
        # x shape
        # [batch_size, sequence_length, embedding_dim]
        # ----------------------------------------------------
        batch_size = x.shape[0]
        sequence_length = x.shape[1]

        # ----------------------------------------------------
        # 1. 입력 X로부터 Q, K, V 생성
        # ----------------------------------------------------

        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)

        # 현재 shape
        '''
        Q shape: [batch_size, sequence_length, embedding_dim]
        K shape: [batch_size, sequence_length, embedding_dim]
        V shape: [batch_size, sequence_length, embedding_dim]
        '''

        # ----------------------------------------------------
        # 여러 Head로 분리
        # ----------------------------------------------------

        Q = Q.reshape(
            batch_size,
            sequence_length,
            self.num_heads,
            self.head_dim
        )

        K = K.reshape(
            batch_size,
            sequence_length,
            self.num_heads,
            self.head_dim
        )

        V = V.reshape(
            batch_size,
            sequence_length,
            self.num_heads,
            self.head_dim
        )
        # [batch, sequence, head, head_dim]



        # ----------------------------------------------------
        # Head를 앞으로 이동
        # ----------------------------------------------------
        Q = Q.transpose(1, 2) # [batch, head, sequence, head_dim]
        K = K.transpose(1, 2) 
        V = V.transpose(1, 2)

        # ----------------------------------------------------
        # 2. Key의 마지막 두 차원 교환
        # ----------------------------------------------------

        K_T = K.transpose(
            -2,
            -1,
        )

        # ----------------------------------------------------
        # 2. Q와 K의 유사도 계산
        # ----------------------------------------------------

        attention_score = (
            Q @ K_T
        )
        # [batch, head, sequence, sequence]

        # ----------------------------------------------------
        # 3. Scaling
        # ----------------------------------------------------

        scaled_score = (
            attention_score
            / (self.head_dim ** 0.5)
        )


        # ----------------------------------------------------
        # 4. Softmax
        # ----------------------------------------------------

        attention_weights = F.softmax(
            scaled_score,
            dim=-1,
        )


        # ----------------------------------------------------
        # 5. 각 Head의 Attention결과
        # ----------------------------------------------------

        head_output = (
            attention_weights @ V
        )
        # [batch, head, sequence, head_dim]


        # ----------------------------------------------------
        # Head 위치를 다시 원래대로 이동
        # ----------------------------------------------------

        head_output = head_output.transpose(1, 2)
        # [batch, sequence, head, head_dim]

        # ----------------------------------------------------
        # 여러 Head를 하나로 합치기
        # ----------------------------------------------------
        concat_output = head_output.reshape(
            batch_size, sequence_length, self.embedding_dim
        )
        # [batch, sequence, embedding]

        output = self.output_linear(concat_output)

        return (
            output,
            attention_weights,
            Q,
            K,
            V,
            head_output,
            concat_output
        )


# ============================================================
# 2. 입력 데이터
# ============================================================

words = [
    "나는",
    "사과를",
    "먹는다",
]


sentence = [
    [1.0, 0.0, 1.0, 0.0],   # 나는
    [0.0, 2.0, 0.0, 2.0],   # 사과를
    [1.0, 1.0, 1.0, 1.0],   # 먹는다
]

X = torch.tensor(
    [
        sentence
    ],
    dtype = torch.float32
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

embedding_dim = 4
num_heads = 2

model = SimpleMultiHeadAttention(
    embedding_dim=embedding_dim,
    num_heads = num_heads
)


# ============================================================
# 4.  실행
# ============================================================

(
    output,
    attention_weights,
    Q,
    K,
    V,
    head_output,
    concat_output
) = model(X)


# ============================================================
# 5. Q 확인
# ============================================================

print("\n" + "=" * 60)
print("Query")
print("=" * 60)

print(Q)

# ============================================================
# 8. Attention Weight 확인
# ============================================================

print("\n" + "=" * 60)
print("Attention Weights")
print("=" * 60)

print(attention_weights)
print(f'attention_weight shape: {attention_weights.shape}')

# ============================================================
# Head별 결과
# ============================================================
print("\n" + "=" * 60)
print("Head Output")
print("=" * 60)
print(head_output)
print(f'head_output shape: {head_output.shape}')

# ============================================================
# Head 결합 결과
# ============================================================
print("\n" + "=" * 60)
print("Concat Output")
print("=" * 60)
print(concat_output)
print(f'concat_output shape: {concat_output.shape}')


# ============================================================
# 최종 출력 결과
# ============================================================
print("\n" + "=" * 60)
print("final Output")
print("=" * 60)
print(output)
print(f'final_output shape: {output.shape}')


