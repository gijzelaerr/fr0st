from runscript import *

flame = Flame(file="samples.flame",name="julia")

from timeit import Timer

print flame.to_string()
##print flame.gradient.formatstr

print Timer("flame.gradient.to_string()",
            "from __main__ import flame").timeit(1000)


