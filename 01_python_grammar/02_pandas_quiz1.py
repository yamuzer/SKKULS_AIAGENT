# 1. 아래 코드를 이용하여 데이터 프레임을 구성한다.
import pandas as pd
import numpy as np
myindex = ['김구', '이봉창', '안중근', '윤봉길']
mycolumns = ['강남구', '은평구', '마포구', '용산구']
mylist = list(10 * onedata for onedata in range(1, 17))
frame = pd.DataFrame(np.reshape(mylist, (4,4)),
                     index = myindex,
                     columns = mycolumns)
print(frame)
print()
#ㄱ.1번째 행 데이터를 조회
print(frame.iloc[[1]])
print()
#ㄴ.1번째와 3번째 행 데이터를 조회
print(frame.iloc[[1,3]])
print()
#ㄷ.'윤봉길'행만 조회
print(frame.loc[['윤봉길']])
print()
#ㄹ.'이봉창'과 '윤봉길' 행을 조회
print(frame.loc[['이봉창','윤봉길']])
print()
#ㅁ.'윤봉길'행의 '은평구' 데이터만 조회
print(frame.loc[['윤봉길'], '은평구'])
print()
#ㅂ.'김구'와 '이봉창'의 '용산구'와 '은평구' 데이터 조회
print(frame.loc[['김구','윤봉길'], ['용산구','은평구']])
print()
#ㅅ.'은평구'의 값이 100이하인 행들을 조회
print(frame['은평구'] <= 100)
print()
print(frame[frame['은평구'] <= 100])
print(frame.loc[frame['은평구'] <= 100])
#ㅇ.'은평구'의 값인 100인 행들을 조회
print()
print(frame.loc[frame['은평구'] == 100])
print()

#ㅈ.'김구'부터 '안중근' 까지 '용산구' 데이터를 80으로 변경
print(frame.loc['김구':'안중근', ['용산구']])
print()
frame.loc['김구':'안중근', ['용산구']] = 80
print(frame)

