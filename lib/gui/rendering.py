import wx

from decorators import Locked


@Locked
def render(genome,size,quality,estimator=9,**kwds):
    """Passes render requests on to flam3."""
    width,height = size
    genome.pixels_per_unit /= genome.width/float(width) # Adjusts scale
    genome.width = width
    genome.height = height
    genome.sample_density = quality
    genome.estimator = estimator
    output_buffer, stats = genome.render(**kwds)
    return wx.BitmapFromBuffer(width, height, output_buffer)

##@Locked
##def render(genome,size,quality,estimator=9,**kwds):
##    return wx.EmptyBitmap(size[0],size[1],32)
