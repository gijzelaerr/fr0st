from __future__ import generators

#Copyright (c) 2008 Vitor Bosshard
#This program licensed under the GPL. See license.txt for details.
#
#Tested under:
#Python 2.6.1
#Pygame 1.8.1.win32-py2.5
#-----------------------------------------------------------------

# This code sets up the namespace in which fr0st scripts run

import os, sys, marshal, copy, random, cmath, shutil, numpy, colorsys, itertools, types
from math import *
sys.dont_write_bytecode = False # Why is this line here?

#-------------------------------------------------------------------------------
#Experimental thingy for script window map function
def range_gen(x, y, n, curve='lin', a=1):
    last = 0
    prev = x
    m = float(n)

    if curve=='par':
        d = (y-x)/(a*m)**2
        rangefunc = lambda: (x+a*d*((last+1)**2)) 
    elif curve=='npar':
        d = (x-y)/(a*m)**2
        prev = -y
        rangefunc = lambda: (x+a*d*((n-(last+1))**2))
    elif curve=='cos':
        d = y-x
        rangefunc = lambda: ((x+d*((cos(pi + ((last+1)/m)*pi))+1)/2)**a)
    elif curve=='sinh':
        d = y-x
        rangefunc = lambda: (((sinh(a*(2*(last+1)-m)/m) - sinh(-a)) / (2*sinh(a*(2*n-m)/m)/d))+x)
    elif curve=='tanh':
        d = y-x
        rangefunc = lambda: (((tanh(a*(2*(last+1)-m)/m) - tanh(-a)) / (2*tanh(a*(2*n-m)/m)/d))+x)
    else:
        d = (y-x)/m
        rangefunc = lambda: (x+d*(last+1))
    while last < n:
        val = rangefunc()
        yield val-prev
        prev = val
        last += 1

        if last == n:
            last = 0
            prev = x
            
def vector_gen(cps, n, curve='lin', a=1.0, t=0.5, loop=False):
    if loop:
        v = []
        cps = cps[-1:] + cps[:-1]
        for i in xrange(len(cps)):
            vt = vector(cps[:4], n, curve, a=1.0, t=0.5)
            v += vt[:-1]
            cps = cps[1:] + cps[:1]
    else:
        v = vector(cps, n, curve, a=1.0, t=0.5)
    v2 = v[1:] + v[:1]
    def diff(x,y): return y-x
    v=map(diff,v,v2)
    itr = itertools.cycle(v)
    return itr

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
interp - Sort of the front-end to interpolation system. It will determine if you
    are interpolating 1, 2, or 3-dimensional data and handle it accordingly.
    There are also options for generating looping vectors that can be smoothed
    with Cardinal Splines. You need at least 4 points for smoothing to work (or
    3 and looping), otherwise it falls back on linear.
    
    Curve allows you to create a curved vector between two control points. The
    parameter "a" allows you to modify the slope of the curve. Supported curve
    types are:
        - lin - Line
        - par - Parabolic curve (starts slow, ends fast)
        - npar - Negative parabolic curve (starts fast, ends slow)
        - cos - Half-period cosine wave
        - sinh - Hyperbolic sine
        - tanh - Hyperbolic tangent
    
    If you chose smooth interpolation type, t will adjust the tension of the
    spline. Negative numbers result in peaks while higher numbers cause larger
    estimation curves. Catmull-Rom is the default (0.5)
    
    Space is a setting only for color and coordinate interpolation. In color
    interpolation, you have the choice between rgb and hls interpolations. For
    coordinate interpolation you can chose between rect and polar options.
    
  cps    - List of control points
  n      - Distance (steps) between control points
  curve  - Curve type of the interpolation
  a      - Curve parameter (mostly tied to slope)
  t      - Spline tension
  smooth - Use smoothing spline
  loop   - Create looping vector
"""
def interp(cps, n, curve='lin', a=1.0, t=0.5, smooth=False, loop=False,
           space='rgb'):

    #Determine which interpolation function to use           
    if type(cps[0])==types.TupleType:
        if len(cps[0])==2:                  #2-tuple = coordinate
            ifunc=pinterp
            if space=='rgb':                #switch space to something related
                space = 'rect'
        else:
            ifunc=cinterp                   #3-tuple = color
    else:
        ifunc=vector                        #non-tuple = point

    #4 types are handled - looping, smooth, looping and smooth, and none
    if loop:
        if smooth and len(cps)>2:
            v = []
            #if not enough for splines, append first onto last and continue
            if len(cps)==3: cps = cps + cps[:1]
            #vector does middle 2 on smooth, so rotate 1 to 2
            cps = cps[-1:] + cps[:-1]
            for i in xrange(len(cps)):
                v += ifunc(cps[:4], n, curve, a, t, space)
                cps = cps[1:] + cps[:1]
        else:
            v = []
            for i in xrange(len(cps)):
                v += ifunc(cps[:2], n, curve, a, space)
                cps = cps[1:] + cps[:1]
    else:
        if smooth and len(cps)>3:
            v = ifunc(cps[:4], n, curve, a, t, space)
        else:
            v = ifunc(cps[:2], n, curve, a, space)
    return v

"""
drange - Returns a list of values from x to y over n steps.
  x     - starting value
  y     - ending value
  n     - number of steps (returned list is n items long ending with y)
  curve - lin, par, npar, cos, sinh, tanh
  a     - curve param
"""
def drange(x, y, n, curve='lin', a=1):
    v = []
    m = float(n)
    if curve=='par':
        d = (y-x)/((a*m)**2)
        for i in xrange(1,n+1):
            v.append(x+a*d*(i**2))
    elif curve=='npar':
        d = (y-x)/((a*m)**2)
        for i in xrange(1,n+1):
            v.append(y-a*d*((n-i)**2))
    elif curve=='cos':
        d = y-x
        for i in xrange(1,n+1):
            v.append((x+d*((cos(pi + (i/m)*pi))+1)/2)**a)
    elif curve=='sinh':
        d = y-x
        for i in xrange(1,n+1):
            v.append(((sinh(a*(2*i-m)/m) - sinh(-a)) / (2*sinh(a*(2*n-m)/m)/d))+x)
    elif curve=='tanh':
        d = y-x
        for i in xrange(1,n+1):
            v.append(((tanh(a*(2*i-m)/m) - tanh(-a)) / (2*tanh(a*(2*n-m)/m)/d))+x)
    else:
        d = (y-x)/m
        for i in xrange(1,n+1):
            v.append(x+d*i)
    return v

"""
vector - Returns a vector between control points
  cps - list of control points (min 4 required for Cardinal Splines)
  n - distance between control points
  curve - curve of the line between the two points to be smoothed
  a - curve parameter
  t - tension of the spline (0.5 = Catmull-Rom)
"""
def vector(cps, n, curve='lin', a=1, t=0.5, space=None):
    pk = []
    if len(cps)>1 and len(cps)<4:
        d = cps[1] - cps[0]
        v = drange(0,1,n,curve,a)
        for i in v:
            pk.append(cps[0]+i*d)
    elif len(cps)>=4:
        cps = cps[:4]
        dy = cps[2]-cps[1]
        v = drange(0,1,n,curve,a)
        cps = numpy.array(cps)
        M = numpy.array([[0,1,0,0]
                        ,[-t,0,t,0]
                        ,[2*t,t-3,3-2*t,-t]
                        ,[-t,2-t,t-2,t]])
        W = []
        
        for i in v:
            vtmp = []
            for j in xrange(4):
                vtmp.append(i**j)
            W.append(vtmp)

        W = numpy.array(W)
        print cps
        vp = numpy.dot(M,cps)
        p = numpy.dot(W,vp)
        for i in xrange(len(p)):
            pk.append(p[i])
    return pk

"""
pinterp - Helper for point interpolation
  space - rect or polar
"""    
def pinterp(cps, n, curve='lin', a=1.0, t=0.5, space='rect'):
    if space=='polar':
        for i in cps:
            i = polar(i)
        xcps = []
        ycps = []
        for i in cps:
            xcps.append(i[0])
            ycps.append(i[1])
        px = vector(xcps, n, curve, a, t)
        py = vector(ycps, n, curve, a, t)
        pk = []
        for i in xrange(n):
            pk.append(rect((px[i],py[i])))
    else:
        xcps = []
        ycps = []
        for i in cps:
            xcps.append(i[0])
            ycps.append(i[1])
        px = vector(xcps, n, curve, a, t)
        py = vector(ycps, n, curve, a, t)
        pk = []
        for i in xrange(n):
            pk.append((px[i],py[i]))
    return pk

"""
cinterp - Helper for interpolating colors
"""
def cinterp(cps, n, curve='cos', a=1.0, t=0.5, space='rgb'):
    rcps = []
    gcps = []
    bcps = []
    for i in cps:
        if space=='hls':
            r,g,b = rgb2hls(i)
        else:
            r,g,b = i
        rcps.append(r)
        gcps.append(g)
        bcps.append(b)
    r = vector(rcps, n, curve, a, t)
    g = vector(gcps, n, curve, a, t)
    b = vector(bcps, n, curve, a, t)
    pk = []    
    for i in xrange(len(r)):
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
    g1 = interp([comp, lspl], dist, curve)
    #g2 is from dist to 128 (seed)
    g2 = interp([lspl, seed], 128-dist, curve)
    #g3 is from 127 to 255-dist
    g3 = interp([seed, rspl], 128-dist, curve)
    #g4 is from 255-dist to 255
    g4 = interp([rspl, comp], dist, curve)
    
    return g1+g2+g3+g4

def from_seeds(seeds, curve='cos', space='rgb'):
    ns = len(seeds)
    d = 256/ns
    r = 256%ns
    ds = []
    for i in xrange(ns):
        if i+1<=r: ds.append(d+1)
        else:      ds.append(d)
    g = []
    for i in xrange(ns):
        tmp = interp([seeds[i-1], seeds[i]], ds[i], curve, space=space)
        g += tmp
    return g

