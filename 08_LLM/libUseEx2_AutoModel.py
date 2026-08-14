from transformers import AutoTokenizer, AutoModel

MODEL_NAME = 'klue/bert-base'

#Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

#transformer 모델
model = AutoModel.from_pretrained(MODEL_NAME)

model.eval()

text = '나는 오늘 학교에서 인공지능을 공부한다.'
print(f'\n원문: {text}')

inputs = tokenizer(
    text,
    return_tensors='pt'
)

print('\nTokenizer 결과:')
print(inputs)

print('\ninput ids:')
print(inputs['input_ids'])
print(f"shape: {inputs['input_ids'].shape}")

import torch

with torch.no_grad():
    output = model(**inputs)


# 모델 출력

#print('\n모델 출력')
#print(output)
'''
last_hidden_state = output.last_hidden_state
print('\nlast hidden state')
print(last_hidden_state)
print(last_hidden_state.shape)
'''

print('\ntoken별 transformer 출력')
last_hidden_state = output.last_hidden_state

tokens = tokenizer.convert_ids_to_tokens(
    inputs["input_ids"][0]
)

#print(tokens)
for index, token in enumerate(tokens):
    token_vector = last_hidden_state[0,index]
    print(f'{token:15s} -> {token_vector}')
    print(f'token shape:{token_vector.shape}', end='\n\n')