from sklearn.feature_extraction.text import TfidfVectorizer

corpus = [
    'I love deep learning i love apple',
    'I love NLP',
    'I enjoy flying'
]

vectorizer = TfidfVectorizer()

vectorizer.fit(corpus)
print(vectorizer.vocabulary_)

x = vectorizer.transform(corpus)
print(x)
print()
print(x.toarray())