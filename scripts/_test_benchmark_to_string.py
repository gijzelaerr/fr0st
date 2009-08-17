from time import time

t = time()
for i in range(1000):
    flame.to_string()
print "to string avg ms:  ", time() - t

s = flame.to_string()

t = time()
for i in range(1000):
    Flame(string=s)
print "from string avg ms:", time() - t