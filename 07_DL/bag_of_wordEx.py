import numpy as np

corpus = [
    'I love deep learning i love apple',
    'I love NLP',
    'I enjoy flying'
]

word = set(' '.join(corpus).lower().split())
print(word)
word2idx = {w: i for i, w in enumerate(sorted(word))}
print(word2idx)

def bow_vector(sentence):
    vec = np.zeros(len(word2idx), dtype=int)
    for word in sentence.lower().split():
        if word in word2idx:
            vec[word2idx[word]] += 1
    return vec

print()
for s in corpus:
    print(f'{s} -> {bow_vector(s)}')