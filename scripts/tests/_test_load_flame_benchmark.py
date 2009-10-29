import time

s = flame.to_string()

t = time.time()

for i in range(1000):
    Flame(s)

print time.time() - t