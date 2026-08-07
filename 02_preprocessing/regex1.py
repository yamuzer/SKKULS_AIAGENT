import re
rc = re.compile('world')
print(rc)

rdata = re.search(rc, 'hello world it is')
print(rdata)
print(rdata.span())
print(rdata.group())
print(rdata.group(0))
print()

rdata2 = re.search(r'world', 'hello world it is')
print(rdata2)

rdata3 = re.match(r'world', 'hello world it is')
print(rdata3)

fdata = re.findall(r'world', 'hello world it is')
print(fdata)

fdata2 = re.findall(r'a*b', 'ab bb ccc abc')
print(fdata2)

fdata3 = re.findall(r'a+b', 'ab bb ccc abc')
print(fdata3)

fdata4 = re.findall(r'[0-9]+', 'hello world12 8863 gd42ec')
print(fdata4)

fdata4 = re.findall(r'[0-9]+-[0-9]+-[0-9]+', 'tel:010-7878-8989')
print(fdata4)

fdata4 = re.findall(r'[0-9]{3}-[0-9]{4}-[0-9]{4}', 'tel:010-7878-8989')
print(fdata4)

fdata4 = re.findall(r'[0-9]{2,3}-[0-9]{3,4}-[0-9]{4}', 'tel:010-7878-8989 phone:017-789-7878' 'home: 02-788-5656')
print(fdata4)

fdata5 = re.findall(r'a.b', 'ab bb aabcc aaab abc')
print(fdata5)

fdata5 = re.findall(r'a?b', 'ab bb aabcc aaab abc')
print(fdata5)

fdata6 = re.findall(r'[a-zA-Z0-9-]+', 'tel:010-7878-8989 phone:017-789-7878' 'HOME: 02-788-5656 Good tEL')
print(fdata6)

fdata6 = re.findall(r'[^a-z]+', 'tel:010-7878-8989 phone:017-789-7878' 'HOME: 02-788-5656 Good tEL')
print(fdata6)

fdata7 = re.findall(r'[가-힣]+', 'tel:010-7878-8989 안녕하세요 phone:017-789-7878' 'HOME: 02-788-5656 Good tEL')
print(fdata7)

fdata7 = re.findall(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', 'tel:010-7878-8989 안녕하세요 phone:017-789-7878' 'HOME: 02-788-5656 Good ㅋㅋㅋㅋ ㅐㅐ ㅠㅠ tEL')
print(fdata7)

fdata8 = re.findall(r'\d{2,3}-\d{3,4}-\d{4}', 'tel:010-7878-8989 안녕하세요 phone:017-789-7878' 'HOME: 02-788-5656 Good ㅋㅋㅋㅋ ㅐㅐ ㅠㅠ tEL')
print(fdata8)

fdata8 = re.findall(r'[a-zA-Z0-9_]+', 'tel:010-7878-8989 안녕하세요 phone:017-789-7878' 'HOME: 02-788-5656 Good ㅋㅋㅋㅋ ㅐㅐ ㅠㅠ tEL func_10 _abc')
print(fdata8)

fdata8 = re.findall(r'\w+', 'tel:010-7878-8989 안녕하세요 phone:017-789-7878' 'HOME: 02-788-5656 Good ㅋㅋㅋㅋ ㅐㅐ ㅠㅠ tEL')
print(fdata8)

fdata8 = re.findall(r'\W+', 'tel:010-7878-8989 안녕하세요 phone:017-789-7878' 'HOME: 02-788-5656 Good ㅋㅋㅋㅋ ㅐㅐ ㅠㅠ tEL')
print(fdata8)

fdata8 = re.findall(r'\s+', 'tel:010-7878-8989    \n    안녕하세요 phone:017-789-7878' 'HOME: 02-788-5656 Good ㅋㅋㅋㅋ ㅐㅐ ㅠㅠ tEL')
print(fdata8)

