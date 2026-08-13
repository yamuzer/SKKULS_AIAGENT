import torch
import torch.nn as nn
import unidecode
import string
import random

total_epochs = 2000
chunk_len = 200

hidden_size = 100
batch_size = 1
num_layer = 1
embedding = 70
learning_rate = 0.002

print(string.printable)
all_characters = string.printable
n_characters = len(all_characters)
print(n_characters)

file = unidecode.unidecode(open('input.txt').read())
#print(file)
file_len = len(file)
print(file_len)

def random_chunk():
    start_index = random.randint(0, file_len - chunk_len)
    end_index = start_index + chunk_len + 1
    return file[start_index: end_index]

def char_tensor(string):
    tensor = torch.zeros(len(string)).long()
    for c in range(len(string)):
        tensor[c] = all_characters.index(string[c])
    return tensor

#print(char_tensor('good'))

class RNNet(nn.Module):
    def __init__(self, input_size, embedding_size, hidden_size, output_size, num_layers=1):
        super().__init__()
        self.input_size = input_size
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers

        self.encoder = nn.Embedding(self.input_size, self.embedding_size)
        self.rnn = nn.LSTM(self.embedding_size, self.hidden_size, num_layers)
        self.fc = nn.Linear(self.hidden_size, self.output_size)

    def init_hidden(self):
        hidden = torch.zeros(self.num_layers, batch_size, hidden_size)
        cell = torch.zeros(self.num_layers, batch_size, hidden_size)
        return hidden, cell

    def forward(self, input, hidden, cell):
        x = self.encoder(input.view(1, -1))
        out, (hidden, cell) = self.rnn(x, (hidden, cell))
        y = self.fc(out.view(batch_size, -1))
        return y, hidden, cell

model = RNNet(input_size=n_characters,
              embedding_size=embedding,
              hidden_size=hidden_size,
              output_size=n_characters,
              num_layers=num_layer)
loss_func = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

def random_train_set():
    chunk = random_chunk()
    input = char_tensor(chunk[:-1])
    target = char_tensor(chunk[1:])
    return input, target

def test():
    start_str = 'b'
    input = char_tensor(start_str)
    hidden, cell = model.init_hidden()

    for i in range(200):
        output, hidden, cell = model(input, hidden, cell)
        output_dist = output.data.view(-1).div(0.8).exp()
        top_i = torch.multinomial(output_dist, 1)[0]
        predicted_char = all_characters[top_i]
        print(predicted_char, end='')
        input = char_tensor(predicted_char)

for epoch in range(total_epochs):
    input, label = random_train_set()
    hidden, cell = model.init_hidden()
    loss = torch.tensor([0]).type(torch.FloatTensor)
    optimizer.zero_grad()
    for j in range(chunk_len - 1):
        x_train = input[j]
        y_train = label[j].unsqueeze(dim=0).type(torch.LongTensor)
        hypothesis, hidden, cell = model(x_train, hidden, cell)
        loss += loss_func(hypothesis, y_train)
    loss.backward()
    optimizer.step()

    if epoch % 50 == 0:
        print('='*200)
        print(f'loss:{loss.item() / chunk_len:4f}', end='\n\n')
        test()
        print('\n','='*200, end='\n\n')












