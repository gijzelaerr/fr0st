import numpy as np
cimport numpy as np
import random as rn

"""
palette_improve
get_length
pix_diff
pix_swap
spline
cdiff
curve
"""

def palette_improve(np.ndarray[ndim=2, dtype=np.float32_t] orig, int ntries,\
         int trysize):
    cdef np.ndarray[ndim=2, dtype=np.float32_t] best = orig.copy()
    cdef np.ndarray[ndim=2, dtype=np.float32_t] pal
    cdef int best_len = get_length(best)
    cdef int j, i, i0, i1, as_is, swapd, pal_len
    for i in range(ntries):
        pal = best.copy()
        for j in range(256):
            pix_swap(pal, j, rn.randint(0, 255))
        pal_len = get_length(pal)
        for j in range(trysize):
            i0 = (1 + rn.randint(0,253))
            i1 = (1 + rn.randint(0,253))
            if i0-i1==1:
                as_is = (pix_diff(pal, i1-1, i1) +
                        pix_diff(pal, i0, i0+1))
                swapd = (pix_diff(pal, i1-1, i0) +
                        pix_diff(pal, i0, i1+1))
            elif i1-i0==1:
                as_is = (pix_diff(pal, i0-1, i0) +
                      pix_diff(pal, i1, i1+1))
                swapd = (pix_diff(pal, i0-1, i1) +
                        pix_diff(pal, i1, i0+1))
            else:
                as_is = (pix_diff(pal, i0, i0+1) +
                        pix_diff(pal, i0, i0-1) +
                        pix_diff(pal, i1, i1+1) +
                        pix_diff(pal, i1, i1-1))
                swapd = (pix_diff(pal, i1, i0+1) +
                        pix_diff(pal, i1, i0-1) +
                        pix_diff(pal, i0, i1+1) +
                        pix_diff(pal, i0, i1-1))
            if swapd < as_is:
                pix_swap(pal, i0, i1)
                pal_len += (swapd - as_is)
                #end trysize loop
        if pal_len < best_len:
            best = pal.copy()
            best_len = pal_len
        #end ntries loop
    for i in xrange(256):
        i0 = (1 + rn.randint(0, 252))
        i1 = i0 + 1
        as_is = (pix_diff(best, i0-1, i0) +
            pix_diff(best, i1, i1+1))
        swapd = (pix_diff(best, i0-1, i1) +
            pix_diff(best, i0, i1+1))
        if swapd < as_is:
            pix_swap(best, i0, i1)
    return best

def get_length(np.ndarray[ndim=2, dtype=np.float32_t] pal):
    cdef int length = 0
    cdef int i
    for i in range(1,256):
        length += pix_diff(pal, i, i-1)
    return length

def pix_diff(np.ndarray[ndim=2, dtype=np.float32_t] pal, int i0, int i1):
    cdef int diff = 0
    cdef int i
    for i in range(3):
        diff += (pal[i0,i] - pal[i1,i])**2
    return diff

def pix_swap(np.ndarray[ndim=2, dtype=np.float32_t] pal, int i0, int i1):
    cdef int i
    cdef float tmp
    for i in range(3):
        tmp = pal[i0,i]
        pal[i0,i] = pal[i1,i]
        pal[i1,i] = tmp

def spline(np.ndarray[ndim=1, dtype=np.float32_t] cps,
           np.ndarray[ndim=1, dtype=np.int32_t] times,
           int ti=0, int ci=-1, int bi=0, int to=0, int co=-1, int bo=0,
           int curve=-1, float amp=0, int freq=1, float slope=1,
           int mode=0, float peak=0.5):

    cdef np.ndarray[ndim=1, dtype=np.float32_t] results
    cdef float cona, conb, conc, cond
    cdef float h00, h01, h10, h11
    cdef float tani, tano
    cdef int step = 0
    cdef float i = 0.0
    cdef int dt0, dt1, dt2
    cdef float dv0, dv1, dv2

    results = np.zeros(times[2]-times[1], dtype=np.float32)

    cona = (1-ti)*(1-bi)*(1+ci)*0.5
    conb = (1-ti)*(1+bi)*(1-ci)*0.5
    conc = (1-to)*(1-bo)*(1-co)*0.5
    cond = (1-to)*(1+bo)*(1+co)*0.5

    dv0 = cps[1] - cps[0]
    dv1 = cps[2] - cps[1]
    dv2 = cps[3] - cps[2]
    dt0 = times[1] - times[0]
    dt1 = times[2] - times[1]
    dt2 = times[3] - times[2]

    while step < dt1:
        h00 = 2*i**3 - 3*i**2 + 1
        h01 = -2*i**3 + 3*i**2
        h10 = i**3 - 2*i**2 + i
        h11 = i**3 - i**2

# ralf  q(k) = (x(k+1)-2*x(k) + x(k-1))/(x(k+1)-x(k-1))
        tani =  cona*dv0 + conb*(dv1)
        tano =  conc*dv1 + cond*dv2
        if not (ti==0 and ci==-1 and bi==0): tani *= 2*dt1/(dt1+dt0)
        if not (to==0 and co==-1 and bo==0): tano *= 2*dt2/(dt2+dt1)

        results[step] = h00*cps[1] + h01*cps[2] + h10*tani + h11*tano
        if curve<>-1: results[step] += cdiff(dv1, i, curve, amp, freq, slope, peak, mode)
        i += 1.0/float(dt1)
        step += 1
    return results

"""
Curve types:
    non-parametric: 0 - lin, 1 - par, 2 - npar
    w/ slope 3 - hcos, 4 - sinh, 5 - tanh, 6 - exp
    w/ amp + freq + slope: 7 - cos, 8 - sin
    w/ amp + peak: 9 - plin, 10 - ppar (w/mode - 0=--, 1=-+, 2=+-, 3=++)
"""
def cdiff(float d, float i, int curve=0, float amp=0, int freq=1, float slope=1,
          float peak=0.5, int mode=0):
    cdef float val

    if i==0: return 0.0

    if curve==-1:
        return 0.0
    elif curve==0:
        if d==0 and amp==0: return 0.0
        val = (d + amp) * i
    elif curve==1:
        if d==0 and amp==0: return 0.0
        val = (d + amp) * i**2
    elif curve==2:
        if d==0 and amp==0: return 0
        val = (d + amp) * (1 - (1-i)**2)
    elif curve==3:
        if d==0 and amp==0: return 0.0
        val = (0.5*(d+amp)*(np.cos((i+1)*np.pi)+1))**slope
    elif curve==4:
        if d==0: return 0.0
        val = (np.sinh((2*i-1)*slope) + np.sinh(slope))/(2*np.sinh(slope))/d
    elif curve==5:
        if d==0: return 0.0
        val = (np.tanh((2*i-1)*slope) + np.tanh(slope))/(2*np.tanh(slope))/d
    elif curve==6:
        if d==0 and amp==0: return 0.0
        val = (d+amp) * ((1-np.exp(-slope*i))/(1-np.exp(-slope)))
    elif curve==7:
        if freq<=0:
            raise ValueError('Frequency much be positive non-zero')
        if amp==0: return 0.0
        val = (0.5*amp*(np.cos(2*freq*i*np.pi + np.pi)+1))**slope + i*d
    elif curve==8:
        if freq<=0:
            raise ValueError('Frequency must be positive non-zero')
        if amp==0: return 0.0
        val = amp*np.sin(i*np.pi*2*freq) + i*d
        if np.sign(val**slope) <> np.sign(val):
            val = val**slope * np.sign(val)
        else:
            val = val**slope
    elif curve==9:
        if peak <= 0.0 or peak >= 1.0:
            raise ValueError('peak need to be 0-1')
        if amp==0: return 0.0
        if  i <= peak: val = i * (amp/peak)
        elif i > peak: val = (1-i)*(amp/(1-peak))
        val += i*d
    elif curve==10:
        if peak <= 0.0 or peak >= 1.0:
            raise ValueError('peak need to be 0-1')
        if mode < 0 or mode > 3:
            raise ValueError('invalid mode')
        if amp==0: return 0.0
        elif mode==0:
            if  i <= peak: val = amp * (1-(1-(i/peak))**2)
            elif i > peak: val = amp * (1-(1-((1-i)/(1-peak)))**2)
        elif mode==1:
            if  i <= peak: val = amp * (1-(1-(i/peak))**2)
            elif i > peak: val = amp * ((1-i)/(1-peak))**2
        elif mode==2:
            if  i <= peak: val = amp * (i/peak)**2
            elif i > peak: val = amp * (1-(1-((1-i)/(1-peak)))**2)
        elif mode==3:
            if  i <= peak: val = amp * (i/peak)**2
            elif i > peak: val = amp * ((1-i)/(1-peak))**2
        val += i*d
    else:
        raise ValueError('invalid curve')

    return val - i*d

"""
pblend
  s = starting value
  e = ending value
  i = which value to grab (normalized between 0-1)
  curves=0 - lin
         1 - cos
"""
def pblend(float s, float e, float i, int curve=0):
    if i==0: return s
    elif i==1: return e

    if s==e: return s

    if curve==0:
        return s + ((e-s) * i)
    elif curve==1:
        return s + (0.5*(e-s)*(np.cos((i+1)*np.pi)+1))
    else:
        raise ValueError('invalid curve')
