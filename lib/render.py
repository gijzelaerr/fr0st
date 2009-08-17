import sys

from pyflam3 import Genome
from lib.fr0stlib import Flame
from ctypes import *

if 'win' in sys.platform:
    from pyflam3 import _flam4


def render(*a, **k):
    renderer = k["renderer"]
    if renderer == "flam3":
        return _flam3_render(*a, **k)
    elif renderer == "flam4":
        return _flam4_render(*a, **k)
    else:
        raise ValueError("Invalid renderer: %s" % renderer)
    

def _flam3_render(flame, size, quality, estimator=9, fixed_seed=False, **kwds):
    """Passes render requests on to flam3."""
    if type(flame) is str:
        string = flame
    else:
        string = flame.to_string()
        
    try:
        genome = Genome.from_string(string)[0]
    except Exception:
        raise ValueError("Error while parsing flame string.")
        
    width,height = size

    try:
        genome.pixels_per_unit /= genome.width/float(width) # Adjusts scale
    except ZeroDivisionError:
        raise ZeroDivisionError("Size passed to render function is 0.")
    
    genome.width = width
    genome.height = height
    genome.sample_density = quality
    genome.estimator = estimator
    output_buffer, stats = genome.render(fixed_seed=fixed_seed, **kwds)
    return output_buffer


def _flam4_render(flame, size, quality, estimator=9, fixed_seed=False, **kwds):
    """Passes requests on to flam4. Works on windows only for now."""
    kwds['channels'] = 4 # Needs to be forced.
    flam4Flame = _flam4.loadFlam4(flame)
    output_buffer = _flam4.renderFlam4(flam4Flame,size)
    return output_buffer
