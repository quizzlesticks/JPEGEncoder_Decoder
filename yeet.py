import numpy as np

a = np.zeros((34,24),dtype=np.uint8)

row = 0
col = 0
a[8*row:8*row+8, 8*col:8*col+8] = np.zeros((8,8)) + 1
row = 1
col = 1
a[8*row:8*row+8, 8*col:8*col+8] = np.zeros((8,8)) + 2
row = 1
col = 2
a[8*row:8*row+8, 8*col:8*col+8] = np.zeros((8,8)) + 3

for i in range(24):
	print(a[i])

