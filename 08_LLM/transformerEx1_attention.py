import torch
import torch.nn.functional as F

# 입력
words = [
    '나는',
    '사과를',
    '먹는다'
]

# embedding 통과 후 vector 값
X = torch.tensor(
    [
        [1.0, 0.0, 1.0, 0.0],    #나는
        [0.0, 2.0, 0.0, 2.0],    #사과를
        [1.0, 1.0, 1.0, 1.0]     #먹는다
    ],
    dtype=torch.float32
)

torch.manual_seed(42)

embedding_dim = X.shape[1]


# Q, K, V 가중치
W_Q = torch.randn(embedding_dim, embedding_dim)
W_K = torch.randn(embedding_dim, embedding_dim)
W_V = torch.randn(embedding_dim, embedding_dim)


# Q, K, V 생성
Q = X @ W_Q
K = X @ W_K
V = X @ W_V

print('\n' + '=' * 100)
print('Q')
print('=' * 100)
print(Q)

print('\n' + '=' * 100)
print('K')
print('=' * 100)
print(K)

print('\n' + '=' * 100)
print('V')
print('=' * 100)
print(V)


# Q와 K의 유사도 계산
attention_score = Q @ K.T
print('\n' + '=' * 100)
print('Attention Score Q @ K.T')
print('=' * 100)
print(attention_score)


# Scaling

 
d_k = Q.shape[-1]

scaled_score = attention_score / (d_k ** 0.5)
print('\n' + '=' * 100)
print('scaled attention score')
print('=' * 100)
print(scaled_score)

# softmax

attention_weights = F.softmax(
                        scaled_score, 
                        dim=-1
                    )

print('\n' + '=' * 100)
print('attention weigths')
print('=' * 100)
print(attention_weights)

# 각 행(단어(token)) attention weight 합
print('\n각 행의 합')
print(attention_weights.sum(dim=-1))

# V를 이용하여 최종 결과 생성

output = attention_weights @ V

print('\n' + '=' * 100)
print('attention output')
print('=' * 100)
print(output)

# 단어별 attention

print('\n' + '=' * 100)
print('단어별 attention')
print('=' * 100)

for i, query_word in enumerate(words):
    print(f'\n[{query_word}]가 참고하는 정도')
    for j, key_word in enumerate(words):
        weight = attention_weights[i,j].item()
        print(f'{key_word:6s} : {weight:.4f}')

print(end='\n\n')
print('=' * 100)


