from lib.pyflam3 import Genome

flame = Flame(file="samples.flame",name="julia")

import time

t = time.time()
for i in range(1000):
    Genome.from_string(flame.to_string())

print time.time() - t


