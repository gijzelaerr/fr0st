from lib.pyflam3 import flam3_colorhist, Genome, flam3_xform_preview, RandomContext
from ctypes import c_double

genome = Genome.from_string(self.flame.to_string())[0]
#array = (c_double *256)()
#flam3_colorhist(genome, 1, array)


array = (c_double *100)()

flam3_xform_preview(genome, 0, 1, 3, 1, array, RandomContext())


print array[:]




