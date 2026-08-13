import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.datasets as dset
import torchvision.transforms as transforms
from torch.utils.data import DataLoader

train_epochs = 10
batch_size = 100

train_data = dset.MNIST('MNIST_data/',
                            train=True,
                            download=True,
                            transform=transforms.ToTensor())

test_data = dset.MNIST('MNIST_data/',
                        train=False,
                        download=True,
                        transform=transforms.ToTensor())

data_loader = DataLoader(dataset=train_data,
                         batch_size=batch_size,
                         shuffle=True,
                         drop_last=True)

class CNNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.layer2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.fc = nn.Linear(64 * 7 * 7, 10)

    def forward(self, x):
        out = self.layer1(x)
        out = self.layer2(out)
        out = out.view(out.size(0), -1)
        y = self.fc(out)
        return y


model = CNNet()
loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
total_batch = len(data_loader)

for epoch in range(train_epochs):
    avg_loss = 0
    for x_train, y_train in data_loader:
        optimizer.zero_grad()
        hypothesis = model(x_train)
        loss = loss_func(hypothesis, y_train)
        loss.backward()
        optimizer.step()
        avg_loss += loss / total_batch
    print(f'epoch:{epoch+1} avg_loss:{avg_loss:.4f}')

    with torch.no_grad():
        x_test = test_data.test_data.view(len(test_data), 1, 28, 28).float()
        y_test = test_data.test_labels
        prediction = model(x_test)
        correction_prediction = torch.argmax(prediction, dim=1) == y_test
        accuracy = correction_prediction.float().mean()
        print(f'accuracy: {accuracy.item() * 100:2.2f}')





















