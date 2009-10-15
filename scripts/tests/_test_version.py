import sys, wx, numpy

from fr0stlib import pyflam3, VERSION

print "python:", sys.version.replace("\n", " ")
print "wx:    ", wx.version()
print "numpy: ", numpy.version.version
print
print "flam3: ", pyflam3.flam3_version()
print "fr0st: ", VERSION
