import sys, wx, numpy

from lib.pyflam3 import flam3_version


print "python:", sys.version
print "flam3: ",flam3_version()
print "wx:    ", wx.version()
print "numpy: ", numpy.version.version