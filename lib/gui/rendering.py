import wx, time
from threading import Thread

from decorators import Catches, Threaded
from _events import ThreadMessageEvent
from ..pyflam3 import Genome


def render(string,size,quality,estimator=9,**kwds):
    """Passes render requests on to flam3."""
    genome = Genome.from_string(string)[0]
    width,height = size
    # HACK!
    try:
        genome.pixels_per_unit /= genome.width/float(width) # Adjusts scale
    except:
        pass
    genome.width = width
    genome.height = height
    genome.sample_density = quality
    genome.estimator = estimator
    output_buffer, stats = genome.render(**kwds)
    return output_buffer


class Renderer():
    def __init__(self, parent):
        self.parent = parent
        self.previewqueue = []
        self.bgqueue = []
        self.thumbqueue = []
        self.exitflag = None
        self.previewflag = 0
        self.bgflag = 0
        self.RenderLoop()
        self.bgRenderLoop()


    def ThumbnailRequest(self,callback,metadata,*args,**kwds):
        """Schedules a genome to be rendered as soon as there are no previous
        or higher priority requests pending."""
        self.thumbqueue.append((callback,metadata,args,kwds))


    def PreviewRequest(self,callback,metadata,*args,**kwds):
        """Schedules a render immediately after the current render is done.
        Cancels previous urgent requests (assuming they are obsolete), but
        leaves the normal request queue intact."""
        self.previewflag = 1
        self.previewqueue = [(callback,metadata,args,kwds)]

        
    def LargePreviewRequest(self,callback,metadata,*args,**kwds):
        """Makes a preview request with a callback function."""
        prog_func = kwds.get("progress_func", None)
        if not prog_func:
            raise KeyError("You must specify a progress function")
        kwds["progress_func"] = self.prog_wrapper(prog_func, "previewflag")
        self.previewflag = 1
##        self.previewqueue = [(callback,metadata,args,kwds)]
        # This is an append so that a simultaneous request for small and
        # large previews goes through.
        self.previewqueue.append((callback,metadata,args,kwds))


    def RenderRequest(self,callback,metadata,*args,**kwds):
        """Makes a render request run in a different thread than previews,
        so it can be paused."""
        prog_func = kwds.get("progress_func", None)
        if not prog_func:
            raise KeyError("You must specify a progress function")
        kwds["progress_func"] = self.prog_wrapper(prog_func, "bgflag")

        self.bgqueue = [(callback,metadata,args,kwds)]
        

    @Threaded
    @Catches(TypeError)
    def RenderLoop(self):
        while not self.exitflag:
            queue = self.previewqueue or self.thumbqueue
            if queue:
                callback,metadata,args,kwds = queue.pop(0)
                self.previewflag = 0
                self.bgflag = 2 # Pauses the other thread
                output_buffer = render(*args,**kwds)
                self.bgflag = 0
                evt = ThreadMessageEvent(callback,metadata,output_buffer)
                wx.PostEvent(self.parent,evt)
            else:
                time.sleep(.01)  # Ideal interval needs to be tested


    @Threaded
    @Catches(TypeError)
    def bgRenderLoop(self):
        while not self.exitflag:
            if self.bgqueue:
                callback,metadata,args,kwds = self.bgqueue.pop(0)
                output_buffer = render(*args,**kwds)
                evt = ImageReadyEvent(callback,metadata,output_buffer)
                wx.PostEvent(self.parent,evt)
            else:
                time.sleep(.01)
        

    def prog_wrapper(self, f, flag):
        def prog_func(*args):
            res = f(*args)
            return max(getattr(self,flag), res)
        return prog_func

    
