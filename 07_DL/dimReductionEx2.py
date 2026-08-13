from sklearn.datasets import load_breast_cancer

cancer = load_breast_cancer()
print(len(cancer.feature_names))

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

scaler = StandardScaler()
x_scaled = scaler.fit_transform(cancer.data)

pca = PCA(n_components=2)
x_pca = pca.fit_transform(x_scaled)
print(x_pca.shape)

import mglearn
plt.figure(figsize=(10,10))
mglearn.discrete_scatter(x_pca[:, 0], x_pca[:, 1], cancer.target)
plt.legend(['악성','양성'], loc='best')
plt.xlabel('첫번째 주성분')
plt.ylabel('두번째 주성분')
plt.show()




