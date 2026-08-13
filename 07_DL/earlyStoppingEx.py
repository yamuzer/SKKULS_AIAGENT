import torch
import torchvision.datasets as dset
import torchvision.transforms as transforms
from  torch.utils.data import DataLoader
import numpy as np

torch.manual_seed(111)
from torch.utils.data.sampler import SubsetRandomSampler

def create_datasets(batch_size):
    train_data = dset.MNIST('MNIST_data/',
                            train=True,
                            download=True,
                            transform=transforms.ToTensor())
    test_data = dset.MNIST('MNIST_data/',
                            train=False,
                            download=True,
                            transform=transforms.ToTensor())

    num_train = len(train_data)
    indices = list(range(num_train))
    np.random.shuffle(indices)
    split = int(np.floor(0.2*num_train))
    train_idx, valid_idx = indices[split:], indices[:split]

    train_sampler = SubsetRandomSampler(train_idx)
    valid_sampler = SubsetRandomSampler(valid_idx)

    train_loader = DataLoader(train_data, sampler=train_sampler, batch_size=batch_size)
    valid_loader = DataLoader(train_data, sampler=valid_sampler, batch_size=batch_size)
    test_loader = DataLoader(test_data, batch_size=batch_size)

    return train_loader, test_loader, valid_loader

import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class ImageNN(nn.Module):
    def __init__(self, drop_p=0.5):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 10)

        self.dropout_p = drop_p

    def forward(self, x):
        x = x.view(-1, 784)
        out = F.relu(self.fc1(x))
        out = F.dropout(out, p=self.dropout_p, training=self.training)
        out = F.relu(self.fc2(out))
        out = F.dropout(out, p=self.dropout_p, training=self.training)
        y = self.fc3(out)
        return y

model = ImageNN(drop_p=0.5)
loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters())

class EarlyStopping:
    def __init__(self, patience=7, verbose=False, delta=0, path='checkpoint.pt'):
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.inf
        self.delta = delta
        self.path = path

    def save_checkpoint(self, val_loss, model):
        if self.verbose:
            print(f'validation loss:({self.val_loss_min:.6f}) -> ({val_loss:.6f}) saving model!!!')
        torch.save(model.state_dict(), self.path)
        self.val_loss_min = val_loss

    def __call__(self, val_loss, model):
        score = val_loss
        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
        elif score > self.best_score + self.delta:
            self.counter += 1

            if self.counter > self.patience:
                self.early_stop = True
            else:
                print(f'earlyStopping counter : {self.counter} / {self.patience}')
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
            self.counter= 0

def train_model(model, patience, n_epochs):
    train_losses = []
    valid_losses = []
    avg_train_losses = []
    avg_valid_losses = []
    early_stopping = EarlyStopping(patience=patience, verbose=True)

    for epoch in range(1, n_epochs+1):
        model.train()
        for x_train, y_train in train_loader:
            optimizer.zero_grad()
            hypothesis = model(x_train)
            loss = loss_func(hypothesis, y_train)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        model.eval()
        for x_data, target in valid_loader:
            output = model(x_data)
            loss = loss_func(output, target)
            valid_losses.append(loss.item())

        train_loss = np.mean(train_losses)
        valid_loss = np.mean(valid_losses)
        avg_train_losses.append(train_loss)
        avg_valid_losses.append(valid_loss)
        epoch_len = len(str(n_epochs))

        print(f'[{epoch:<{epoch_len}} / {n_epochs:>{epoch_len}}]'+
              f'train_loss:{train_loss:.5f} valid_loss:{valid_loss:.5f}')

        train_losses = []
        valid_losses = []

        early_stopping(valid_loss, model)

        if early_stopping.early_stop:
            print('early stopping!!!!!')
            break

    model.load_state_dict(torch.load('checkpoint.pt'))

    return model, avg_train_losses, avg_valid_losses


batch_size = 256
n_epochs = 100

train_loader, test_loader, valid_loader = create_datasets(batch_size)
patience = 10
model, train_loss, valid_loss = train_model(model, patience, n_epochs)






