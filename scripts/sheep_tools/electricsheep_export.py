"""
Converts a flame compatible with fr0st (flam3 2.8) to one compatible
with electricsheep (flam3 2.7)
"""

from itertools import chain
from fr0stlib.pyflam3.variations import variations

# VAR_PARABOLA (53) is the highest supported variation.
unsupported = set(k for (k,v) in variations.items() if v > 53)

def check_compatibility(flame):
    problems = []
    if any(x.opacity != 1 for x in flame.xform):
        problems.append("  -opacity not supported")

    for x in flame.xform:
        if any(i != 1 for i in x.chaos):
            problems.append("  -chaos not supported")
            break

    if flame.highlight_power != -1:
        problems.append("  -highlight power not supported")

    bad_vars = unsupported & set(chain(*(x.list_variations()
                                         for x in flame.xform)))
    problems.extend("  -%s variation not supported" %i
                    for i in bad_vars)

    return problems


def convert(flame):
    problems = check_compatibility(flame)
    if problems:
        print '"%s" can\'t be converted:' %flame.name
        print "\n".join(problems)
        print
        return
    for x in flame.xform:
        x.symmetry = 1. - x.color_speed * 2
        del x.color_speed

    flame.version = "flam3 2.7"


map(convert, get_flames())
