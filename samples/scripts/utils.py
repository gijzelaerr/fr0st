"""
This file contains several utility functions that can be imported
from other scripts, through the standard python import mechanism.
"""

import itertools, fr0stlib

def calculate_colors(xforms):
    """Distribute color values evenly among xforms. You can pass the entire
    xform list as an argument, or just a slice of it."""
    len_ = len(xforms) - 1.0 or 1.0
    for i, xf in enumerate(xforms):
        xf.color = i / len_


def normalize_weights(flame, norm=1.0):
    """Normalize the weights of the xforms so that they total 1.0"""
    ws = sum(xf.weight for xf in flame.xform) / norm
    for xf in flame.xform:
        xf.weight /= ws

        
def batch(func, nflames, *a, **k):
    """Takes a flame-generating function, and calls it multiple
    times to generate a batch."""
    name = func.__name__ + "%03d"
    lst = []
    for i in range(nflames):
        flame = func(*a, **k)
        flame.name = name % i
        lst.append(flame)
    return lst


def animation_preview(flames, repeat=True):
    """ animate flames in an infinite loop."""
    assert fr0stlib.GUI # guard against command line scripts.
    itr = itertools.cycle(flames) if repeat else flames
    for f in itr:
        fr0stlib.preview(f)
        fr0stlib.show_status("previewing %s" %f)

               
