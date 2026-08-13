import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

sentences = [
    'i like deep learning',
    'i like pytorch',
    'pytorch is great for deep learning',
    'we enjoy coding in pytorch'
]

words = ' '.join(sentences).split()
vocab = sorted(set(words))
vocab_size = len(vocab)
word2idx = {w : i for i, w in enumerate(vocab)}
idx2word = {i : w for w, i in word2idx.items()}
print(vocab)
print(vocab_size)
print(word2idx)
print(idx2word)

window_size = 2
pairs = []
for sentence in sentences:
    tokens = sentence.split()
    for center_idx in range(len(tokens)):
        for w in range(-window_size, window_size + 1):
            context_idx = center_idx + w
            if context_idx < 0 or context_idx >= len(tokens) or center_idx == context_idx:
                continue
            pairs.append((word2idx[tokens[center_idx]], word2idx[tokens[context_idx]]))
print(pairs)

class Word2Vec(nn.Module):
    def __init__(self, vocab_size, embedding_dim):
        super().__init__()
        self.w_in = nn.Parameter(torch.randn(vocab_size, embedding_dim))
        self.b_in = nn.Parameter(torch.zeros(embedding_dim))

        self.w_out = nn.Parameter(torch.randn(vocab_size, embedding_dim))
        self.b_out = nn.Parameter(torch.zeros(vocab_size))

    def forward(self, center_word_idx):
        h = self.w_in[center_word_idx] + self.b_in
        y = torch.matmul(h, self.w_out.T) + self.b_out
        return y, h

embedding_dim = 8
model = Word2Vec(vocab_size, embedding_dim)
optimizer = optim.Adam(model.parameters(), lr=0.01)
loss_func = nn.CrossEntropyLoss()

for epoch in range(300):
    total_loss = 0
    for center, context in pairs:
        center = torch.tensor([center])
        context = torch.tensor([context])

        output, h = model(center)
        loss = loss_func(output, context)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    if epoch % 10 == 0:
        print(f'epoch:{epoch +1} | loss:{total_loss / len(pairs):.4f}')

w_in = model.w_in.detach().numpy()
b_in = model.b_in.detach().numpy()
print(w_in)
print(w_in.shape)

print('\nembedding matrix (w_in) 예시')
for w in ['pytorch', 'learning', 'coding', 'deep']:
    idx = word2idx[w]
    print(f'{w:10s} -> {np.round(w_in[idx],4)}')

from sklearn.decomposition import PCA

pca = PCA(n_components=2)
reduced = pca.fit_transform(w_in)
import matplotlib.pyplot as plt
plt.figure(figsize=(8,6))
for i, word in enumerate(vocab):
    plt.scatter(reduced[i, 0], reduced[i, 1])
    plt.text(reduced[i, 0] + 0.02, reduced[i, 1] + 0.02, word)
plt.title('word2vec embedding space(PCA 2D)')
plt.show()











