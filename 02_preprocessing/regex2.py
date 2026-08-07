import re
robj1 = re.search(r'([0-9]+) ([0-9]+)', 'good 3232 323 hell 3232')
print(robj1)
print(robj1.group())
print(robj1.group(1))
print(robj1.group(2))
print()

robj2 = re.search(r'([a-zA-Z_][a-zA-z0-9_]+)\((\w+)\)', 'good _insa(hello111) info good job')
print(robj2)
print(robj2.group(0))
print(robj2.group(1))
print(robj2.group(2))

robj2 = re.search(r'(?P<func>[a-zA-Z_][a-zA-z0-9_]+)\((?P<arg>\w+)\)', 'good _insa(hello111) info good job')
print(robj2.group('func'))
print(robj2.group('arg'))

text = '새로운 뉴스는 2026-007-28에 발표됩니다.'
'''
전체 날짜 : 2026-07-28
연도 : 2026
월 : 07
일 : 28
'''

robj3 = re.search(r'(?P<year>\d{4})-(?P<month>\d{3})-(?P<day>\d{2})', text)
print(robj3)
print(robj3.group('year'))
print(robj3.group('month'))
print(robj3.group('day'))
print()

cstr1 = re.sub(r'apple|orange', 'fruit', 'apple box orange box')
print(cstr1)

def multi_ten(match):
    n = int(match.group())
    return str(n * 10)

cstr2 = re.sub(r'[0-9]+', multi_ten, 'function23 812 value:50')
print(cstr2)
print()

cstr3 = re.sub(r'(a-z+)(0-9+)', r'\2 \1 \2 \1', 'hello good 784 32')
print(cstr3)

# greedy
fdata1 = re.findall(r'<b>.+</b>', '<b>is good </b><b>website</b>contain a body')
print(fdata1)

# lazy
fdata1 = re.findall(r'<b>.+?</b>', '<b>is good </b><b>website</b>contain a body')
print(fdata1)

