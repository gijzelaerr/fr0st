from fr0stlib.pyflam3 import Genome
from fr0stlib import Flame, needs_conversion


def flam3_render(flame, size, quality, **kwds):
    """Passes render requests on to flam3."""
    if isinstance(flame, basestring):
        if needs_conversion(flame):
            genome = Genome.from_string(Flame(flame).to_string())[0]
        else:
            genome = Genome.from_string(flame)[0]
    else:
        genome = Genome.from_string(flame.to_string())[0]

    width,height = size

    try:
        genome.pixels_per_unit /= genome.width/float(width) # Adjusts scale
    except ZeroDivisionError:
        raise ZeroDivisionError("Size passed to render function is 0.")
    
    genome.width = width
    genome.height = height
    genome.sample_density = quality
    output_buffer, stats = genome.render(**kwds)
    return output_buffer


def flam4_render(flame, size, quality, **kwds):
    """Passes requests on to flam4. Works on windows only for now."""
    from fr0stlib.pyflam3 import _flam4
    flame = flame if type(flame) is Flame else Flame(flame)
    flam4Flame = _flam4.loadFlam4(flame)
    output_buffer = _flam4.renderFlam4(flam4Flame, size, quality, **kwds)
    return output_buffer

