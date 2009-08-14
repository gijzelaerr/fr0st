from pyflam3 import Genome
from lib.fr0stlib import Flame
from ctypes import *


def render(*a, **k):
    renderer = k["renderer"]
    if renderer == "flam3":
        return _flam3_render(*a, **k)
    elif renderer == "flam4":
        return _flam4_render(*a, **k)
    else:
        raise ValueError("Invalid renderer: %s" % renderer)
    

def _flam3_render(string, size, quality, estimator=9, fixed_seed=False, **kwds):
    """Passes render requests on to flam3."""
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


def _flam4_render(string, size, quality, estimator=9, fixed_seed=False, **kwds):
    """Stub for future flam4 compatibility."""
    flame = Flame(string=string)
