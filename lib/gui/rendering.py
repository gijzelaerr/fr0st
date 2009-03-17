import wx, time
from threading import Thread

from decorators import Catches, Threaded
from _events import ImageReadyEvent
from ..pyflam3 import Genome

def render(string,size,quality,estimator=9,**kwds):
    """Passes render requests on to flam3."""
    genome = Genome.from_string(string)[0]
    width,height = size
    genome.pixels_per_unit /= genome.width/float(width) # Adjusts scale
    genome.width = width
    genome.height = height
    genome.sample_density = quality
    genome.estimator = estimator
    output_buffer, stats = genome.render(**kwds)
    return output_buffer


class Renderer():
    def __init__(self,parent):
        self.parent = parent
        self.urgent = []
        self.queue = []
        self.exitflag = None
        self.RenderLoop()

    def Request(self,callback,metadata,*args,**kwds):
        """Schedules a genome to be rendered as soon as there are no previous
        or higher priority requests pending."""
        self.queue.append((callback,metadata,args,kwds))

    def UrgentRequest(self,callback,metadata,*args,**kwds):
        """Schedules a render immediately after the current render is done.
        Cancels previous urgent requests (assuming they are obsolete), but
        leaves the normal request queue intact."""
        self.urgent = [(callback,metadata,args,kwds)]

    @Threaded
    @Catches(TypeError)
    def RenderLoop(self):
        while not self.exitflag:
##            if self.exitflag:
##                return
            queue = self.urgent or self.queue
            if queue:
                callback,metadata,args,kwds = queue.pop(0)
                output_buffer = render(*args,**kwds)
                evt = ImageReadyEvent(callback,metadata,output_buffer)
                wx.PostEvent(self.parent,evt)
            else:
                time.sleep(.01)  # Ideal interval needs to be tested

