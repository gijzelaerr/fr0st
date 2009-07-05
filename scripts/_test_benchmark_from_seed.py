from timeit import Timer
from time import time


seeds = ((128,50,50), (0,128,255))


t = time()
for i in range(100):
    flame.gradient.from_seeds(seeds)
print time() -t

#print Timer('flame.gradient.from_seeds(seeds)',
#      'from __main__ import preview').timeit(1000)

preview()