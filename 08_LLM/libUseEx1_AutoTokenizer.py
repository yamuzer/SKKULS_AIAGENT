from transformers import AutoTokenizer

MODEL_NAME = 'klue/bert-base'

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

text = '나는 오늘 학교에서 인공지능을 공부한다.'
print(f'\n원문 : {text}')
'''
tokens = tokenizer.tokenize(text)
print('\nToken: ')
print(tokens)

token_ids = tokenizer.convert_tokens_to_ids(tokens)
print('\n Token ID: ')
print(token_ids)
'''

inputs = tokenizer(
    text,
    return_tensor='pt' #pytorch
)
print('\n tokenizer 결과')
print(inputs)