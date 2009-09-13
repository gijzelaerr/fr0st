import os, sys, cmath, numpy, colorsys, random
from math import *

hues = {'red': 0,
        'orange': 1/12.0,
        'yellow': 1/6.0,
        'lime': 0.25,
        'green': 1/3.0,
        'turquois': 5/12.0,
        'cyan': 0.5,
        'lblue': 7/12.0,
        'blue': 2/3.0,
        'purple': 0.75,
        'pink': 5/6.0,
        'magenta': 11/12.0}

#-------------------------------------------------------------------------------
#Utility functions
"""
in_ranges - Returns True if n is in one of the tuple ranges
  n - number to check
  ranges - list of min-max tuples (or single tuple)
"""
def in_ranges(n, ranges):
    if type(ranges)==list:
        for r in ranges:
            if n >= r[0] and n <= r[1]: return True
    else:
        if n >= ranges[0] and n <= ranges[1]: return True
    return False


def randrange2(x,y):
    """A smarter randrange. Returns a random float between both args."""
    return x if x==y else random.randrange(*sorted((x,y)), int=float)
    
#-------------------------------------------------------------------------------
#Converters

def polar(coord):
    l = sqrt(coord[0]**2 + coord[1]**2)
    theta = atan2(coord[1], coord[0]) * (180.0/pi)
    return l, theta   

def rect(coord):
    real = coord[0] * cos(coord[1]*pi/180.0)
    imag = coord[0] * sin(coord[1]*pi/180.0)
    return real, imag


def rgb2hls(color):
    """Takes an rgb tuple (0-255) and returns hls tuple (hls is scalar)"""
    return colorsys.rgb_to_hls(*(x/256. for x in color))

def hls2rgb(color):
    """Takes hls tuple and returns rgb tuple (rgb is int)"""
    #convert h to scalar
    h,l,s = color
    h = clip(h,0,1,True)
    l = clip(l,0,1)
    s = clip(s,0,1)
    return tuple(int(x*256) for x in colorsys.hls_to_rgb(h,l,s))


def rgb2hsv(color):
    return colorsys.rgb_to_hsv(*(x/256. for x in color))

def hsv2rgb(color):
    h,s,v = color
    h = clip(h,0,1,True)
    s = clip(s,0,1)
    v = clip(v,0,1)
    return tuple(int(x*256) for x in colorsys.hsv_to_rgb(h,s,v))
    
    
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
    peak  = kwargs.get('peak',0.5)
    freq  = kwargs.get('freq',1)

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

"""
prange - Periodic range
"""
def prange(x, y, n, i, curve='lin', a=1.0, peak=0.5, freq=1):
    n1=int(peak*n)
    n2=n-n1
    m=float(n)
    
    if curve=='pp-par':     #par up, par down
        if i<n1: return drange(x,y,n1,i,curve='par',a=a)
        else:    return drange(y,x,n2,i-n1,curve='par',a=a)
    elif curve=='pn-par':   #par up, npar down
        if i<n1: return drange(x,y,n1,i,curve='par',a=a)
        else:    return drange(y,x,n2,i-n1,curve='npar',a=a)
    elif curve=='np-par':   #npar up, par down (smooth parabolic shape)
        if i<n1: return drange(x,y,n1,i,curve='npar',a=a)
        else:    return drange(y,x,n2,i-n1,curve='par',a=a)
    elif curve=='nn-par':   #npar up, npar down
        if i<n1: return drange(x,y,n1,i,curve='npar',a=a)
        else:    return drange(y,x,n2,i-n1,curve='npar',a=a)
    elif curve=='sin':      #sine wave (positive and negative)
        d = y-x
        if d<>0: return x+d*sin((i/m)*pi*2*freq)
        else:    return 0
    elif curve=='cos':     #cosine wave (positive only)
        d = y-x
        if d<>0: return (x+d*((cos(pi + (i/m)*pi*2*freq))+1)/2)**a
        else:    return 0
    else:                   #linear
        if i<n1: return drange(x,y,n1,i,curve='lin',a=a)
        else:    return drange(y,x,n2,i-n1,curve='lin',a=a)
#---end prange

def vector(cps, n, i, t=0.5, **kwargs):
    if 1 < len(cps) < 4:
        return drange(cps[0], cps[1], n, i, **kwargs)
    elif len(cps)==4:
##        if cache:
        v = drange(0, 1, n, i, **kwargs)
        cps = numpy.array(cps)
        M = numpy.array(((0,1,0,0)
                        ,(-t,0,t,0)
                        ,(2*t,t-3,3-2*t,-t)
                        ,(-t,2-t,t-2,t)))

        W = numpy.array(v*j for j in range(4))
        vp = numpy.dot(M,cps)
        return numpy.dot(W,vp)
    else:
        #exception code
        print "You have the wrong number of cps."
#---end vector

def vector2d(cps, n, i, p_space='polar', **kwargs):
    if p_space=='polar':
        tmp = []
        for c in cps:
            tmp.append(polar(c))
        cps = tmp

    xcps, ycps = zip(*cps)
    
    if p_space=='polar':
        return rect((vector(xcps,n,i,**kwargs),vector(ycps,n,i,**kwargs)))
    else:
        return (vector(xcps,n,i,**kwargs),vector(ycps,n,i,**kwargs))
#---end vector2d

def vector3d(cps, n, i, c_space='rgb', **kwargs):
    # VBT: commented out because the args are assumed to already be in the
    # target colorspace.
##    if c_space=='hls':
##        cps = [rgb2hls(c) for c in cps]

    rcps, gcps, bcps = zip(*cps)
    
    if c_space=='hls':
        return hls2rgb((vector(rcps,n,i,**kwargs)
                       ,vector(gcps,n,i,**kwargs)
                       ,vector(bcps,n,i,**kwargs)))
    elif c_space=='hsv':
        return hsv2rgb((vector(rcps,n,i,**kwargs)
                       ,vector(gcps,n,i,**kwargs)
                       ,vector(bcps,n,i,**kwargs)))
    else:
        return (clip(vector(rcps,n,i,**kwargs),0,255)
               ,clip(vector(gcps,n,i,**kwargs),0,255)
               ,clip(vector(bcps,n,i,**kwargs),0,255))
#---end vector3d

class cp():
    def __init__(self, val, time, t=0, c=0, b=0):
        self.val = val
        self.time = time
        self.t=t
        self.c=c
        self.b=b
#---end

def get_padded_cp(target, neighbor):
    pad = cp(0, 0)
    if neighbor.time > target.time:
        pad.time = target.time-1
        mod = 1
    else:
        pad.time = target.time+1
        mod = -1
    if type(target.val)==tuple:
        count = len(target.val)
    else:
        count = 1
    if count > 1:
        tmp = []
        for i in xrange(count):
            slope = ((neighbor.val[i] - target.val[i]) /
                     float(neighbor.time - target.time))
            tmp.append(target.val[i]-(slope*mod))
        pad.val = tuple(tmp)
    else:
        slope = ((neighbor.val - target.val) /
                 float(neighbor.time - target.time))
        pad.val = target.val-(slope*mod)
    return pad


def get_spline(cps, **kwargs):
    if type(cps[0].val)==tuple:
        count = len(cps[0].val)
    else:
        count = 1
    if count > 1:
        tmp = []
        for i in xrange(count):
            tmp.append(spline([cp.val[i] for cp in cps], [cp.time for cp in cps]
                              ,(cps[1].t, cps[1].c, cps[1].b)
                              ,(cps[2].t, cps[2].c, cps[2].b)
                              ,**kwargs))
        out = []
        for i in xrange(len(tmp[0])):
            tmp2 = []
            for j in xrange(count):
                tmp2.append(tmp[j][i])
            out.append(tuple(tmp2))
        return out
    else:
        return spline([cp.val for cp in cps], [cp.time for cp in cps]
                     ,(cps[1].t, cps[1].c, cps[1].b)
                     ,(cps[2].t, cps[2].c, cps[2].b)
                     ,**kwargs)


def spline(cps, times, splinea=(0,0,0), splineb=(0,0,0), curve='lin', a=1):
    if times[0]<0:
        for t in times: t -= times[0]
    ta, ca, ba = splinea
    tb, cb, bb = splineb
    n = times[2] - times[1]
    v = []
    for i in xrange(n):
        v.append(drange(0,1,n,i,curve=curve, a=a))
    fa = (1-ta)*(1+ca)*(1+ba)
    fb = (1-ta)*(1-ca)*(1-ba)
    fc = (1-tb)*(1-cb)*(1+bb)
    fd = (1-tb)*(1+cb)*(1-bb)
    M = numpy.array([[-fa,4+fa-fb-fc,-4+fb+fc-fd,fd]
                    ,[2*fa,-6-2*fa+2*fb+fc,6-2*fb-fc+fd,-fd]
                    ,[-fa,fa-fb,fb,0]
                    ,[0,2,0,0]])
    M = M/2.0
    vals = [cps[0] * (2*times[0])/(times[0]+times[1])
           ,cps[1]
           ,cps[2]
           ,cps[3] * (2*times[2])/(times[2]+times[3])]
    C = numpy.array(vals)
    MxC = numpy.dot(M,C)
    S = []
    for t in v:
        S.append(numpy.array([t**3,t**2,t,1]))
    return numpy.dot(numpy.array(S), MxC)
#---end spline

def spline_check(cps):
    tmp = []
    for i in xrange(len(cps)-3):
        tmp.extend(spline(cps[i:i+4]))
    return tmp

def pix_swap(pal, i0, i1):
    tmp = pal[i0]
    pal[i0] = pal[i1]
    pal[i1] = tmp

def pix_diff(pix1, pix2):
    return sum(map(lambda x,y: (y-x)**2, pix1, pix2))

