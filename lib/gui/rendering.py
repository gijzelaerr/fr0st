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
        self.preview = []
        self.queue = []
        self.thumb = []
        self.exitflag = None
        self.cancelrender = False
        self.RenderLoop()

    def ThumbnailRequest(self,callback,metadata,*args,**kwds):
        """Schedules a genome to be rendered as soon as there are no previous
        or higher priority requests pending."""
        self.thumb.append((callback,metadata,args,kwds))

    def PreviewRequest(self,callback,metadata,*args,**kwds):
        """Schedules a render immediately after the current render is done.
        Cancels previous urgent requests (assuming they are obsolete), but
        leaves the normal request queue intact."""
        self.cancelrender = True
        self.preview = [(callback,metadata,args,kwds)]
        
    def LargePreviewRequest(self,callback,metadata,*args,**kwds):
        """Makes a preview request with a callback function."""
        prog_func = kwds.get("progress_func", None)
        if not prog_func:
            raise KeyError("You must specify a progress function")
        kwds["progress_func"] = self.prog_wrapper(prog_func)
        
        self.cancelrender = True
        self.preview = [(callback,metadata,args,kwds)]

    def RenderRequest(self,callback,metadata,*args,**kwds):
        self.queue = [(callback,metadata,args,kwds)]
        

    @Threaded
    @Catches(TypeError)
    def RenderLoop(self):
        while not self.exitflag:
            queue = self.preview or self.queue or self.thumb
            if queue:
                callback,metadata,args,kwds = queue.pop(0)
                self.cancelrender = False
                output_buffer = render(*args,**kwds)
                evt = ImageReadyEvent(callback,metadata,output_buffer)
                wx.PostEvent(self.parent,evt)
            else:
                time.sleep(.01)  # Ideal interval needs to be tested

        # Shutting down, so render needs to be cancelled.
        self.cancelrender = True


    def prog_wrapper(self, f):
        def prog_func(*args):
            res = f(*args)
            return max(int(self.cancelrender), res)
        return prog_func
