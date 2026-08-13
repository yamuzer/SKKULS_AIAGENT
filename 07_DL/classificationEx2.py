import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

x_train = [[1,2,1,1],
           [2,1,3,2],
           [3,1,3,2],
           [4,1,5,5],
           [1,7,5,5],
           [1,2,5,6],
           [1,6,6,6],
           [1,7,7,7]]

y_train = [2,2,2,1,1,1,0,0]

x_train = torch.FloatTensor(x_train)
y_train = torch.LongTensor(y_train)

class softmaxUseModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(4, 3)

    def forward(self,x):
        return self.fc1(x)

model = softmaxUseModel()
optimizer = optim.SGD(model.parameters())

for epoch in range(1000):
    hypothesis = model(x_train)
    loss = F.cross_entropy(hypothesis, y_train)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 100 == 0:
        print(f'epoch:{epoch+1} loss:{loss.item():.4f}')














