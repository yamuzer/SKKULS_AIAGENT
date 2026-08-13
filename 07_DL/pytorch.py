import torch
import numpy as np
'''
t1 = torch.FloatTensor([[1, 2], [3,4]])
print(t1)
print(type(t1))
print(t1.size())
print(t1.dtype)

print()
t2 = torch.tensor([[4,6],[9,10]], dtype=torch.float32)
print(t2)
print(type(t2))
print(t2.dtype)

print()
print(t2.numpy())
print(type(t2.numpy()))

print()

ndata = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.float32)
t3 = torch.from_numpy(ndata)
print(t3)
print(type(t3))

t1 = torch.tensor([1, 2, 3])
t2 = torch.tensor([5, 6, 7])
print(t1)
print(t2)

t3 = t1 + t2
print(t3)
print()

t4 = torch.tensor([[10, 20, 30], [50,60,70]])
print(t4)
print(t4+t1)
print()

t5 = torch.linspace(0, 3, 10)
print(t5)
print(type(t5))
print(torch.exp(t5))
print(torch.log(t5))
print(torch.cos(t5))
print(torch.sin(t5))
print(torch.sqrt(t5))
print(torch.mean(t5))
print()

t6 = torch.tensor([[2, 3, 0], [90, 50, 70]])
print(t6)
print(torch.max(t6))
print(torch.max(t6, dim=1))
print(type(torch.max(t6)))
print(torch.max(t6, dim=1)[0])
print(torch.max(t6, dim=1)[1])
print()


t1 = torch.tensor([1,2,3,4,5,6])
print(t1)
print()

t2  = t1.view(2, 3) # 논리적 변경
print(t2)
print(type(t2))
print(t1.reshape(2,3)) # 물리적 변경

t3 = torch.tensor([[1,2], [3,4], [5,6]])
print(t3)
print()
print(t3.view(-1)) # flatten
print(t3.view(1, -1))
print(t3.view(2, -1))
print(t3.view(3, -1))
print(t3.view(6, -1))
print()


t3 = torch.tensor([[1,2,3],[4,5,6]])
t4 = torch.tensor([[10,20,30],[40,50,60]])
print(t3)
print()
print(t4)

print(torch.cat([t3, t4], dim=0))
print(torch.cat([t3, t4], dim=1))
print()


t1 = torch.tensor([1, 2, 3, 4, 5, 6]).view(3, 2)
t2 = torch.tensor([7, 8, 9, 10, 11, 12]).view(2,3)
print(t1)
print(t2)

t3 = torch.mm(t1, t2) # 행렬곱
print(t3)

print(torch.matmul(t1, t2))
'''
# slicing
t1 = torch.tensor([[1,2,3],[4,5,6]])
print(t1)

print(t1[:, :2])

print(t1 > 4)

print(t1[t1>4])

t1[:,:2] = 40
print(t1)

t1[t1>4] = 1000
print(t1)

# chunk
t2 = torch.tensor([[1,2,3], [4,5,6]])
t3 = torch.tensor([[8,9,10], [11,22,33]])
print(t2)
print(t3)

t4 = torch.cat([t2, t3], dim=0)
print(t4)

print(torch.chunk(t4, 4, dim=0))

for t in t4:
    print(t)

for ts in torch.chunk(t4, 4, dim=0):
    print(ts)

for ts in torch.chunk(t4, 3, dim=1):
    print(ts)

# initialize
import torch.nn.init as init
t1 = init.uniform_(torch.FloatTensor(3, 4))
print(t1)

t2 = init.normal_(torch.FloatTensor(3, 4), mean=10, std=3)
print(t2)

t3 = torch.FloatTensor(torch.randn(3,4))
print(t3)

t4 = init.constant_(torch.Floattensor(3, 4), 100)
print(t4)

# squeezing
t1 = torch.zeros(1, 4)
t2 = torch.zeros(4, 1)
print(t1)
print(t2)

print(torch.squeeze(t1))
print(torch.squeeze(t2))

