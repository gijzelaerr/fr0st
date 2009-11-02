import time

s = flame.to_string()

t = time.time()
for i in range(1000):
    Flame(s)

print "fm", time.time() - t


t = time.time()
for i in range(1000):
    flame.to_string()

print "to", time.time() - t