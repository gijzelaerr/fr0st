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

def rect(coord):
##    comp = cmath.rect(r,phi)
##    return comp.real,comp.imag # Use this once 2.6 is default
    real = coord[0] * cos(coord[1]*pi/180.0)
    imag = coord[0] * sin(coord[1]*pi/180.0)
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

    (r,b,g) = colorsys.hls_to_rgb(h,l,s)
    return (r*255,g*255,b*255)

#-------------------------------------------------------------------------------
"""
drange - Returns a list of values from x to y over n steps
  x - starting value
  y - ending value
  n - number of steps (returned list is n+1 items)
  curve - lin, par, cos, sinh, tanh
  a - curve param
"""
def drange(x, y, n, curve='lin', a=1):
    v = []
    if curve=='par':
        d = (y-x)/(a*float(n)**2)
        for i in xrange(0,n+1):
            v.append(x+a*d*(i**2))
    elif curve=='cos':
        d = y-x
        for i in xrange(0,n+1):
            v.append((x+d*((cos(pi + (i/float(n))*pi))+1)/2)**a)
    elif curve=='sinh':
        d = y-x
        for i in xrange(0,n+1):
            v.append(x+d*(sinh(i/float(n))/sinh(1)))
    elif curve=='tanh':
        d = y-x
        for i in xrange(0,n+1):
            v.append(x+d*(tanh(i/float(n))/tanh(1)))
    else:
        d = (y-x)/float(n)
        for i in xrange(0,n+1):
            v.append(x+d*i)
    return v

"""
vector - Returns a cardinal spline from a list of 4 control points, or if less than 4 linear
  cps - list of control points (4 required - one before and one after the two that are being smoothed)
  n - distance between control points
  curve - curve of the line between the two points to be smoothed (lin, par, cos)
  a - curve parameter
  t - tension of the spline (0.5 = Catmull-Rom)
"""
def vector(cps, n, curve='lin', a=1, t=0.5):
    pk = []
    if len(cps)>1 and len(cps)<4:
        d = cps[1] - cps[0]
        v = drange(0,1,n,curve,a)
        for i in xrange(0, n+1):
            pk.append(cps[0]+v[i]*d)
    elif len(cps)>=4:
        dy = cps[2]-cps[1]
        v = drange(0,1,n,curve,a)
        cps = numpy.array(cps)
        M = numpy.array([[0,1,0,0]
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
pinterp - Helper for point interpolation
  space - rect or polar
"""    
def pinterp(cps, n, curve='lin', space='rect'):
    if space=='polar':
        for i in cps:
            i = polar(i)
        px = vector(cps, n, curve)
        py = vector(cps, n, curve)
        pk = []
        for i in xrange(0,n+1):
            pk.append(rect((px[i],py[i])))
    else:
        px = vector(cps, n, curve)
        py = vector(cps, n, curve)
        pk = []
        for i in xrange(0,n+1):
            pk.append((px[i],py[i]))
    return pk

"""
cinterp - Helper for interpolating colors
"""
def cinterp(cps, n, curve='cos'):
    """
    if curve=='par' and len(cps)<4: # special case for parabolic smoothing - kinda legacy w/ cos
        rmid = abs((cps[1][0]-cps[0][0])/2.0)
        gmid = abs((cps[1][1]-cps[0][1])/2.0)
        bmid = abs((cps[1][2]-cps[0][2])/2.0)
        r1 = vector([cps1[0],rmid],n,curve)
        g1 = vector([cps1[1],gmid],n,curve)
        b1 = vector([cps1[2],bmid],n,curve)
        r2 = vector([cps2[0],rmid],n,curve)
        g2 = vector([cps2[1],gmid],n,curve)
        b2 = vector([cps2[2],bmid],n,curve)
        r2.reverse()
        g2.reverse()
        b2.reverse()
        r = r1[:-1] + r2
        g = g1[:-1] + g2
        b = b1[:-1] + b2
    else:
    """
    r = vector(cps, n, curve)
    g = vector(cps, n, curve)
    b = vector(cps, n, curve)
    pk = []    
    for i in xrange(0,len(r)):
        pk.append((r[i],g[i],b[i]))
    return pk
    
"""
from_seed - Returns a palette from a seed color
  seed - seed color
  csplit - dist from compliment wheel's other side is (can be neg)
  split - dist from seed rspl and lspl are
  dist - distance from compliment in palette index
  curve - type of palette smoothing (splines are not recommended at this time)
"""
def from_seed(seed, csplit=0, split=30,  dist=64, curve='lin'):
    (h,l,s) = rgb2hls(seed)
    split /= 360.0
    csplit /= 360.0
    comp = hls2rgb((h+csplit+0.5,l,s))
    lspl = hls2rgb((h-split,l,s))
    rspl = hls2rgb((h+split,l,s))

    #g1 is from 0 (compliment) to dist (left split)
    g1 = cinterp(comp, lspl, dist, curve)
    #g2 is from dist to 128 (seed)
    g2 = cinterp(lspl, seed, 128-dist, curve)
    #g3 is from 127 to 255-dist
    g3 = cinterp(seed, rspl, 128-dist, curve)
    #g4 is from 255-dist to 255
    g4 = cinterp(rspl, comp, dist, curve)
    
    g1 = g1[:-1]
    g2 = g2[:-1]
    g3 = g3[1:]
    g4 = g4[1:]
    
    return g1+g2+g3+g4

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
