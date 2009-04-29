from __future__ import generators

#Copyright (c) 2008 Vitor Bosshard
#This program licensed under the GPL. See license.txt for details.
#
#Tested under:
#Python 2.6.1
#Pygame 1.8.1.win32-py2.5
#-----------------------------------------------------------------

# This code sets up the namespace in which fr0st scripts run

import os, sys, marshal, copy, random, cmath, shutil, numpy, colorsys, itertools
from math import *
sys.dont_write_bytecode = False # Why is this line here?


def flatten(l):
    result = []
    for el in l:
        if hasattr(el,'__iter__') and not isinstance(el,basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result
    
#-------------------------------------------------------------------------------
#Converters

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
    l = clip(l,0,1)
    s = clip(s,0,1)

    return map(lambda x: int(x*256),colorsys.hls_to_rgb(h,l,s))
    
#-------------------------------------------------------------------------------
#General utils
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

#-------------------------------------------------------------------------------
#Interpolation and smoothing code
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

args:
  cps    - List of control points
  n      - Distance (steps) between control points
  i      - index value to return

kwargs:    
  curve  - Curve type of the interpolation
  a      - Curve parameter (mostly tied to slope)
  t      - Spline tension
  smooth - Use smoothing spline
  loop   - Create looping vector
  p_space- Coordinate interpolation space (rect, polar)
  c_space- Color interpolation space (rgb, hls)
"""
def interp(cps, n, i, **kwargs):
    #Set defaults
    smooth = kwargs.get('smooth',False)
    loop   = kwargs.get('loop',True)
    loops  = True
    #Determine data dimensions
    if type(cps[0])==tuple:
        if len(cps[0])==2:
            ifunc=vector2d
        elif len(cps[0])==3:
            ifunc=vector3d
            kwargs['smooth']=False
        else:
            #exception
            print "Only 1-, 2-, and 3-d variables are supported."
    else:
        ifunc=vector

    if loop:
        if smooth and len(cps)>2:
            #Determine list rotation
            seg = i/n
            cps = cps[seg-1:] + cps[:seg-1]
            #if 3 long pad the non-interpolating point, otherwise cat to 4
            if len(cps)==3: tcps = cps + cps[:1]
            else:           tcps = cps[:4]
            return ifunc(tcps, n, i%n, **kwargs)
        else:
            #Determine list rotation
            cps = cps[i/n:] + cps[:i/n]
            return ifunc(cps, n, i%n, **kwargs)
    else:
        if smooth and len(cps)>3:
            return ifunc(cps[:4], n, i%n, **kwargs)    
        else:
            return ifunc(cps[:2], n, i%n, **kwargs)
#---end interp

def drange(x, y, n, i, **kwargs):
    #Set defaults
    curve = kwargs.get('curve','lin')
    a     = kwargs.get('a',1.0)

    m=float(n)

    if curve=='par':
        d = (y-x)/(m**2)
        return (x+d*(i**2))
    elif curve=='npar':
        d = (y-x)/(m**2)
        return (y-d*((n-i)**2))
    elif curve=='cos':
        d = y-x
        return (x+d*((cos(pi + (i/m)*pi))+1)/2)**a
    elif curve=='sinh':
        d = y-x
        if d<>0: return x+((sinh(a*(2*i-m)/m) - sinh(-a)) / (2*sinh(a*(2*n-m)/m)/d))
        else:    return 0
    elif curve=='tanh':
        d = y-x
        if d<>0: return x+((tanh(a*(2*i-m)/m) - tanh(-a)) / (2*tanh(a*(2*n-m)/m)/d))
        else:    return 0
    else:
        d = (y-x)/m
        return x+d*i
#---end drange

def vector(cps, n, i, **kwargs):
    #Set defaults
    t = kwargs.get('t', 0.5)
        
    if len(cps)>1 and len(cps)<4:
        return drange(cps[0], cps[1], n, i, **kwargs)
    elif len(cps)==4:
        v = drange(0, 1, n, i, **kwargs)
        cps = numpy.array(cps)
        M = numpy.array([[0,1,0,0]
                        ,[-t,0,t,0]
                        ,[2*t,t-3,3-2*t,-t]
                        ,[-t,2-t,t-2,t]])
        W = []
        for j in xrange(4):
            W.append(v**j)

        W = numpy.array(W)
        vp = numpy.dot(M,cps)
        return numpy.dot(W,vp)
    else:
        #exception code
        print "You have the wrong number of cps."
#---end vector

def vector2d(cps, n, i, **kwargs):
    #Set defaults
    p_space = kwargs.get('p_space','polar')
    
    if p_space=='polar':
        tmp = []
        for c in cps:
            tmp.append(polar(c))
        cps = tmp
    xcps = []
    ycps = []
    for c in cps:
        xcps.append(c[0])
        ycps.append(c[1])
    if p_space=='polar':
        return rect((vector(xcps,n,i,**kwargs),vector(ycps,n,i,**kwargs)))
    else:
        return (vector(xcps,n,i,**kwargs),vector(ycps,n,i,**kwargs))
#---end vector2d

def vector3d(cps, n, i, **kwargs):
    #Set defaults
    c_space = kwargs.get('c_space','rgb')
    
    if c_space=='hls':
        tmp = []
        for c in cps:
            tmp.append(rgb2hls(c))
        cps = tmp
    rcps = []
    gcps = []
    bcps = []
    for c in cps:
        rcps.append(c[0])
        gcps.append(c[1])
        bcps.append(c[2])
    if c_space=='hls':
        return hls2rgb((vector(rcps,n,i,**kwargs)
                       ,vector(gcps,n,i,**kwargs)
                       ,vector(bcps,n,i,**kwargs)))
    else:
        return (clip(vector(rcps,n,i,**kwargs),0,255)
               ,clip(vector(gcps,n,i,**kwargs),0,255)
               ,clip(vector(bcps,n,i,**kwargs),0,255))
#---end vector3d

#-------------------------------------------------------------------------------
#Random palette methods

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

