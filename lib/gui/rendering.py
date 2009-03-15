import wx, time
from threading import Thread

from decorators import Locked, Catches


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
##    return wx.BitmapFromBuffer(width, height, output_buffer)
    return output_buffer

# the real function is broken, so we replace it with a stub to allow testing.
##@Locked
##def render(genome,size,quality,estimator=9,**kwds):
##    return wx.EmptyBitmap(size[0],size[1],32)

# Some new experimental stuff:
class Renderer():
    def __init__(self,parent):
        self.parent = parent
        self.requests = []
        self.exitflag = None
        Thread(target=self.RenderLoop).start()

    def AddRequest(self,callback,metadata,*args,**kwds):
        self.requests.append((callback,metadata,args,kwds))

    @Catches(TypeError)
    def RenderLoop(self):
        while 1:
            if self.exitflag:
                return
            if self.requests:
                # Instead of pop(0), a more sophisticated priorization
                # could be used.
                callback,metadata,args,kwds = self.requests.pop(0)
                output_buffer = render(*args,**kwds)
                evt = ImageReadyEvent(callback,metadata,output_buffer)
                wx.PostEvent(self.parent,evt)
            else:
                time.sleep(.05)  # Ideal interval needs to be tested


myEVT_IMAGE_READY = wx.NewEventType()
EVT_IMAGE_READY = wx.PyEventBinder(myEVT_IMAGE_READY, 1)
class ImageReadyEvent(wx.PyCommandEvent):
    def __init__(self,*args):
        wx.PyCommandEvent.__init__(self, myEVT_IMAGE_READY, wx.ID_ANY)
        self._data = args

    def GetValue(self):
        return self._data
