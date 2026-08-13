import numpy as np
import torch
from torchvision import datasets
from torchvision import transforms
import ssl


ssl._create_default_https_context = ssl._create_unverified_context

datasets.FashionMNIST
train_set = datasets.MNIST(root='MNIST_data/',
                           train=True,
                           download=True,
                           transform=transforms.Compose([transforms.ToTensor()])
)

test_set = datasets.MNIST(root='MNIST_data/',
                           train=False,
                           download=True,
                           transform=transforms.Compose([transforms.ToTensor()])
)

from torch.utils.data import DataLoader

batch_size = 100
train_loader = DataLoader(train_set,
                          batch_size=batch_size,
                          shuffle=True,
                          drop_last=True)

import torch.nn as nn

model = nn.Sequential(
    nn.Linear(784, 256),
    nn.ReLU(),
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
)
import torch.optim as optim
loss_func = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.1)

for epoch in range(20):
    avg_loss = 0
    total_batch = len(train_loader)

    for x_train, y_train in train_loader:
        x_train = x_train.view(-1, 28*28)
        optimizer.zero_grad()
        hypothesis = model(x_train)
        loss = loss_func(hypothesis, y_train)
        loss.backward()
        optimizer.step()

        avg_loss += loss / total_batch
    print(f'epoch:{epoch+1}, avg_loss:{avg_loss:.4f}')

import random
import matplotlib.pyplot as plt

with torch.no_grad():
    x_test = test_set.test_data.view(-1, 28*28).float()
    y_test = test_set.test_labels

    prediction = model(x_test)
    correction_prediction = torch.argmax(prediction, dim=1) == y_test
    accuracy = correction_prediction.float().mean()
    print('accuracy : {:2.2f}%'.format(accuracy * 100))
    print()

    r = random.randint(0, len(test_set) - 1)
    x_single_data = test_set.test_data[r:r+1].view(-1, 28*28).float()
    y_single_data = test_set.test_labels[r:r+1]
    print('target label:', y_single_data.item())

    s_prediction = model(x_single_data)
    print('model prediction:', torch.argmax(s_prediction, dim=1).item())

    plt.imshow(test_set.test_data[r:r+1].view(28, 28), cmap='gray')
    plt.show()
















