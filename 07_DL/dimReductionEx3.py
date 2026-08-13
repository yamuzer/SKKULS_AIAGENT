from sklearn.datasets import make_swiss_roll
import matplotlib.pyplot as plt

x, t = make_swiss_roll(n_samples=1000, noise=0.2, random_state=42)
print(x.shape)
print(t.shape)

axes = [-11.5, 14, -2, 23, -12, 15]

# fig  = plt.figure(figsize=(8, 6))
# ax = fig.add_subplot(111, projection='3d')
# ax.scatter(x[:, 0], x[:, 1], x[:, 2], c=t, cmap=plt.cm.hot)
# ax.set_xlim(axes[0:2])
# ax.set_ylim(axes[2:4])
# ax.set_zlim(axes[4:6])
# plt.show()

from sklearn.manifold import LocallyLinearEmbedding

lle = LocallyLinearEmbedding(n_components=2, n_neighbors=10, random_state=42)
x_reduced = lle.fit_transform(x)

fig  = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111)
ax.scatter(x_reduced[:, 0], x_reduced[:, 1], c=t, cmap=plt.cm.hot)
plt.xlabel('z1', fontsize=14)
plt.ylabel('z2', fontsize=14)
plt.grid(True)
plt.show()

from sklearn.manifold import TSNE

tsne = TSNE(n_components=2, random_state=42)
x_reduced_tsne = tsne.fit_transform(x)
fig  = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111)
ax.scatter(x_reduced_tsne[:, 0], x_reduced_tsne[:, 1], c=t, cmap=plt.cm.hot)
plt.xlabel('z1', fontsize=14)
plt.ylabel('z2', fontsize=14)
plt.grid(True)
plt.show()








