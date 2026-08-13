import torch
import torch.nn as nn

vocab_size = 256

x = list((map(ord, 'hello')))
y = list((map(ord, 'hola')))
print(x)
print(y)

x_data = torch.LongTensor(x)
y_data = torch.LongTensor(y)

class Seq2SeqNet(nn.Module):
    def __init__(self, vocab_size, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.encoder = nn.GRU(hidden_size, hidden_size)
        self.decoder = nn.GRU(hidden_size, hidden_size)
        self.fc = nn.Linear(hidden_size, vocab_size)

    def init_state(self, batch_size=1):
        return torch.zeros(1, batch_size, self.hidden_size)


    def forward(self, inputs, targets):
        initstate = self.init_state()
        embedding = self.embedding(inputs).unsqueeze(dim=1)
        encoder_output, encoder_state = self.encoder(embedding, initstate)

        decoder_state = encoder_state
        decoder_input = torch.LongTensor([0]) #start

        outputs = []

        for i in range(targets.size()[0]):
            decoder_input = self.embedding(decoder_input).unsqueeze(dim=1)
            decoder_output, decoder_state = self.decoder(decoder_input, decoder_state)
            foutput = self.fc(decoder_output)
            outputs.append(foutput)
            decoder_input = torch.LongTensor([targets[i]])
        outputs = torch.stack(outputs).squeeze()
        return outputs


seq2seq = Seq2SeqNet(vocab_size, 16)
loss_func = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(seq2seq.parameters(), lr=1e-3)
loss_data = []

for epoch in range(1000):
    hypothesis = seq2seq(x_data, y_data)
    loss = loss_func(hypothesis, y_data)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    loss_data.append(loss.item())

    if epoch % 50 == 0:
        print(f'epoch{epoch+1} loss:{loss.item():.4f}')
        _, top = hypothesis.data.topk(k=1, dim=1)
        print([chr(c) for c in top.squeeze().numpy().tolist()])


