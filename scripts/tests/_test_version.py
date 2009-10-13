import sys, wx, numpy

from lib import fr0stlib, pyflam3

print "python:", sys.version.replace("\n", " ")
print "wx:    ", wx.version()
print "numpy: ", numpy.version.version
print
print "flam3: ", pyflam3.flam3_version()
print "fr0st: ", fr0stlib.VERSION
