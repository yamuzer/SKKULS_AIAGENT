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


class AutoEncoderNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Linear(256, 20)
        )
        self.decoder = nn.Sequential(
            nn.Linear(20, 256),
            nn.ReLU(),
            nn.Linear(256, 784)
        )

    def forward(self, x):
        x = x.view(batch_size, -1)
        eoutput = self.encoder(x)
        y = self.decoder(eoutput).view(batch_size, 1, 28, 28)
        return y

AEModel = AutoEncoderNet()
loss_func = nn.MSELoss()
optimizer = optim.Adam(AEModel.parameters(), lr=learning_rate)

for epoch in range(train_epochs):
    for idx, (x_data, _) in enumerate(data_loader):
        optimizer.zero_grad()
        hypothesis = AEModel(x_data)
        loss = loss_func(hypothesis, x_data)
        loss.backward()
        optimizer.step()
        if idx % 100 == 0:
            print(f'loss:{loss.item():.4f}')

out_img = torch.squeeze(hypothesis.data)
for i in range(3):
    plt.subplot(121)
    plt.imshow(torch.squeeze(x_data[i]).numpy(), cmap='gray')
    plt.subplot(122)
    plt.imshow(torch.squeeze(out_img[i]).numpy(), cmap='gray')
    plt.show()











