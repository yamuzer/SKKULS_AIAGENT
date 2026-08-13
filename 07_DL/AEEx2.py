import torch
import torchvision.datasets as dset
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

train_epochs = 20
batch_size = 100
learning_rate = 0.0002

mnist_train = dset.MNIST('MNIST_data/',
                         train=True,
                         transform=transforms.ToTensor(),
                         download=True)

mnist_test = dset.MNIST('MNIST_data/',
                         train=False,
                         transform=transforms.ToTensor(),
                         download=True)

data_loader = DataLoader(mnist_train, batch_size=batch_size,
                         shuffle=True, drop_last=True)

def add_noise(img):
    noise = torch.randn(img.size()) * 0.3
    noise_img = img + noise
    return noise_img

class AutoEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 12),
            nn.ReLU(),
            nn.Linear(12, 3)
        )

        self.decoder = nn.Sequential(
            nn.Linear(3, 12),
            nn.ReLU(),
            nn.Linear(12, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, 784),
            nn.Sigmoid()
        )

    def forward(self, x):
        eoutput = self.encoder(x)
        doutput = self.decoder(eoutput)
        return eoutput, doutput

model = AutoEncoder()
loss_func = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

def train(model, train_loader):
    avg_loss = 0

    for (image, _) in train_loader:
        x_data = add_noise(image)
        x_data = x_data.view(-1, 784)
        y = image.view(-1, 784)

        _, decoded = model(x_data)
        loss = loss_func(decoded, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        avg_loss += loss.item()
    return avg_loss / len(train_loader)

for epoch in range(train_epochs):
    loss = train(model, data_loader)
    print(f'epoch:{epoch + 1} loss:{loss:.4f}')

sample_data = mnist_train.data[1].view(-1, 784).type(torch.FloatTensor) / 255.

original_x = sample_data[0]
noise_x = add_noise(original_x)
_, recovered_x = model(noise_x)

fig, axes = plt.subplots(1, 3, figsize=(10,10))
import numpy as np
original_img = np.reshape(original_x.data.numpy(), (28,28))
noise_img = np.reshape(noise_x.data.numpy(), (28,28))
recovered_img = np.reshape(recovered_x.data.numpy(), (28,28))

axes[0].set_title('original')
axes[0].imshow(original_img, cmap='gray')
axes[1].set_title('noise and image')
axes[1].imshow(noise_img, cmap='gray')
axes[2].set_title('recovered and image')
axes[2].imshow(recovered_img, cmap='gray')
plt.show()












