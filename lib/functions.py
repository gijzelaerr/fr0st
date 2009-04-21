#Copyright (c) 2008 Vitor Bosshard
#This program licensed under the GPL. See license.txt for details.
#
#Tested under:
#Python 2.6.1
#Pygame 1.8.1.win32-py2.5
#-----------------------------------------------------------------

# This code sets up the namespace in which fr0st scripts run

import os, sys, marshal, copy, random, cmath, shutil, numpy, colorsys
from math import *
sys.dont_write_bytecode = False # Why is this line here?

import fr0stlib
from fr0stlib import Flame, Xform


#-------------------------------------------------------------------------------

def polar(coord):
##    return cmath.polar(complex(*coord)) # Use this once 2.6 is default
    l = sqrt(coord[0]**2 + coord[1]**2)
    theta = atan2(coord[1], coord[0]) * (180.0/pi)
    return l, theta   

def rect(r,phi):
##    comp = cmath.rect(r,phi)
##    return comp.real,comp.imag # Use this once 2.6 is default
    real = r * cos(phi*pi/180.0)
    imag = r * sin(phi*pi/180.0)
    return real, imag
    
#-------------------------------------------------------------------------------
"""
Clip - clips variable if above or below limits
  v - value
  mini - minimum value
  maxi - maximum value
  rotate - if true, above max wraps to min (default false)
"""
def clip(v, mini, maxi, rotate=False):
    if rotate:
        if v > maxi: v = v-maxi+mini
        elif v < mini: v = v+maxi-mini
    else:
        if v > maxi: v = maxi
        elif v < mini: v = mini
    return v

"""
Takes an rgb tuple (0-255) and returns hls tuple (hls is scalar)
"""
def rgb2hls(color):
    return colorsys.rgb_to_hls(*map(lambda x: x/256.0, color))

"""
Takes hls tuple and returns rgb tuple (rgb is int)
"""    
def hls2rgb(color):
    #convert h to scalar
    h,l,s = color
    h = clip(h,0,1,True)

    (r,g,b) = colorsys.hls_to_rgb(h,l,s)

    return (r*255,b*255,g*255)

#-------------------------------------------------------------------------------
"""
drange - Returns a linear list of values from x to y over n steps
  x - starting value
  y - ending value
  n - number of steps (returned list is n+1 items)
"""
def drange(x, y, n):
    v = []
    d = (y-x)/float(n)
    for i in xrange(0, n+1):
        v.append(x+d*i)
    return v

"""
prange - Returns a parabolic list of values from x to y over n steps
  x - start value
  y - end value
  n - number of steps (returned is n+1)
  a - slope of the curve
"""
def prange(x, y, n, a=1):
  v = []
  d = (y-x)/(a*float(n)**2)
  for i in range(0, n+1):
    v.append(x + a*d*(i**2))
  return v

"""
Smooth - Returns a smoothed curve from a list of 4 control points
  cps - list of control points (4 required - one before and one after the two that are being smoothed)
  n - distance between control points
  t - tension of the spline (0.5 = Catmull-Rom)
"""
def smooth(cps, n, t=0.5):
    y0 = cps[1]                     #initial vector location is second control point
    y1 = cps[2]                     #ending location of the vector
    
    dy = y1-y0                      #delta between start and end
    v = drange(0,1,n)
    cps = numpy.array(cps)
    M = numpy.array(
                    [[0,1,0,0]
                    ,[-t,0,t,0]
                    ,[2*t,t-3,3-2*t,-t]
                    ,[-t,2-t,t-2,t]]
                    )
    W = []
    
    for i in xrange(0,n+1):
        vtmp = []
        for j in xrange(0,4):
            vtmp.append(v[i]**j)
        W.append(vtmp)

    W = numpy.array(W)
    vp = numpy.dot(M,cps)
    pk = numpy.dot(W,vp)
    return pk
    
"""
smooth_color - Returns list of smoothed color tuples
  cps - 4 colors, one before and one after the two being smoothed
  n - distance between colors
"""
def smooth_color(c1, c2, n):
    r = interp(c1[0], c2[0],n)
    g = interp(c1[1], c2[1],n)
    b = interp(c1[2], c2[2],n)

    v = []    
    for i in xrange(0,len(r)):
        v.append((r[i],g[i],b[i]))
    return v

def smoother_color(c1,c2,n):
    rmid = abs((c2[0]-c1[0])/2.0)
    gmid = abs((c2[1]-c1[1])/2.0)
    bmid = abs((c2[2]-c1[2])/2.0)

    r1 = pinterp(c1[0],rmid,n)
    g1 = pinterp(c1[1],gmid,n)
    b1 = pinterp(c1[2],bmid,n)
    r2 = pinterp(c2[0],rmid,n)
    g2 = pinterp(c2[1],gmid,n)
    b2 = pinterp(c2[2],bmid,n)

    r2.reverse()
    g2.reverse()
    b2.reverse()

    r = r1[:-1] + r2
    g = g1[:-1] + g2
    b = b1[:-1] + b2

    v = []    
    for i in xrange(0,len(r)):
        v.append((r[i],g[i],b[i]))
    return v

"""
Interp - Returns a linear vector between two control points
  cp1 - first control point
  cp2 - second control point
  n - distance between control points
"""
def interp(cp1, cp2, n):
    d = cp2 - cp1
    v = drange(0,1,n)
    pk = []
    for i in xrange(0, n+1):
        pk.append(cp1+v[i]*d)
    return pk
    
"""
pinterp - Returns a parabolic vector between two control points
  cp1 - first
  cp2 - second
  n - distance between
"""
def pinterp(cp1, cp2, n):
    d = cp2 - cp1
    v = prange(0,1,n)
    pk = []
    for i in xrange(0, n+1):
        pk.append(cp1+v[i]*d)
    return pk

"""
from_seed - Returns a palette from a seed color
"""
def from_seed(self, seed, split=20, dist=64):
    (h,l,s) = rgb2hls(seed)
    split /= 360.0
    comp = hls2rgb((h+0.5,l,s))
    lspl = hls2rgb((h+0.5-split,l,s))
    rspl = hls2rgb((h+0.5+split,l,s))
    
    #g1 is from 0 (compliment) to dist (left split)
    g1 = smoother_color(comp, lspl, dist)
    #g2 is from dist to 128 (seed)
    g2 = smoother_color(lspl, seed, 128-dist)
    #g3 is from 127 to 255-dist
    g3 = smoother_color(seed, rspl, 128-dist)
    #g4 is from 255-dist to 255
    g4 = smoother_color(rspl, comp, dist)
    
    g = g1[:-1]+g2[1:-1]+g3[:1]+g4
    return g

def save_flame(filename,flame):
    save_flames(filename,flame)


def save_flames(filename,*flames):
    lst = [f.to_string() if isinstance(f,Flame) else f for f in flames]
    lst.insert(0, """<flames name="Fr0st Batch">\n""")
    lst.append("""</flames>""")
    head, ext = os.path.splitext(filename)
    if os.path.exists(filename) and ext == ".flame":
        shutil.copy(filename,head + ".bak")
    f = open(filename,"w")
    f.write("".join(lst))
    f.close()


def load_flames(filename,*args):
    """Reads a flame file and returns a list of flame objects, specified
    by index or name. If no flames are specified, returns all flames in the
    file, in order."""
    
    strings = Flame.load_file(filename)
    
    if not args:
        return [Flame(string=i) for i in strings]

    if all(map(lambda x: type(x) is int, args)):
           return [Flame(string=strings[key]) for key in args]

    flames = []
    re_name = re.compile(r'(?<= name=").*?(?=")')
    temp_names = map(lambda x: re_name.findall(x)[0], strings)

    for key in args:
        _type = type(key)
        if _type is str:
            try:
                key = temp_names.index(key)
            except ValueError:
                raise NameError, ' name "%s" not found in %s' %(key,filename)
        elif _type is not int:
            raise TypeError, "Expected flame index or name, got %s" %_type

        flames.append(Flame(string=strings[key]))
        
    return flames
