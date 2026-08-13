import torch
import torch.optim as optim
import numpy as np

sentence = ("if you want to build a ship, don't drum up people together to "
            "collect wood and don't assign them tasks and work, but rather "
            "teach them to long for the endless immensity of the sea")
print(sentence)
char_set = list(set(sentence))
print(char_set)
char_dic = {c:i for i, c in enumerate(char_set)}
print(char_dic)

dic_size = len(char_dic)
print(dic_size)

hidden_size = dic_size
sequence_length = 10
learning_rate = 0.1

x_data = []
y_data = []
for i in range(0, len(sentence)- sequence_length):
    x_str = sentence[i:i+sequence_length]
    y_str = sentence[i+1: i+sequence_length+1]
    #print(i, x_str, '->', y_str)

    x_data.append([char_dic[c] for c in x_str])
    y_data.append([char_dic[c] for c in y_str])

print(x_data[0])
print(y_data[0])
print()

#print(np.eye(10))
x_one_hot = [np.eye(dic_size)[x] for x in x_data]
#print(x_one_hot[0])
x = torch.FloatTensor(x_one_hot)
y = torch.LongTensor(y_data)
print(x.shape)
print(y.shape)

import torch.nn as nn

class RNNet(nn.Module):
    def __init__(self, input_size, hidden_size, layers):
        super().__init__()
        self.rnn = nn.RNN(input_size, hidden_size, num_layers=layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, hidden_size)

    def forward(self, x):
        output, hidden_size = self.rnn(x)
        y = self.fc(output)
        return y

model = RNNet(dic_size, hidden_size, layers=2)
loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

outputs = model(x)
print(outputs.shape)
print(outputs.view(-1, dic_size).shape)

for epoch in range(100):
    optimizer.zero_grad()
    hypothesis = model(x)
    loss = loss_func(hypothesis.view(-1, dic_size), y.view(-1))
    loss.backward()
    optimizer.step()

    predictions = hypothesis.argmax(dim=2)
    #print(predictions.shape)
    predict_str = ''
    for j, result in enumerate(predictions):
        if j == 0:
            predict_str += ''.join([char_set[t] for t in result])
        else:
            predict_str += char_set[result[-1]]
    print(predict_str)
















