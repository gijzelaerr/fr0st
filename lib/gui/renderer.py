import wx, time, sys, traceback
from threading import Thread

from lib.decorators import Catches, Threaded
from lib.render import render
from lib.gui.config import config
from _events import ThreadMessageEvent


class Renderer():
    def __init__(self, parent):
        self.parent = parent
        self.previewqueue = []
        self.bgqueue = []
        self.thumbqueue = []
        self.exitflag = None
        self.previewflag = 0
        self.bgflag = 0
        if "-debug" not in sys.argv:
            # TODO: remove this.
            self.RenderLoop()
            self.bgRenderLoop()


    def ThumbnailRequest(self,callback,metadata,*args,**kwds):
        """Schedules a genome to be rendered as soon as there are no previous
        or higher priority requests pending."""
        kwds["nthreads"] = 1
        kwds["fixed_seed"] = True
        kwds["renderer"] = "flam3"
        
        self.thumbqueue.append((callback,metadata,args,kwds))


    def PreviewRequest(self,callback,metadata,*args,**kwds):
        """Schedules a render immediately after the current render is done.
        Cancels previous requests (assuming they are obsolete), but leaves the
        normal request queue intact."""
        kwds["nthreads"] = 1
        kwds["fixed_seed"] = True
        kwds["renderer"] = config["renderer"]
        self.previewflag = 1
        
        self.previewqueue = [(callback,metadata,args,kwds)]

        
    def LargePreviewRequest(self,callback,metadata,*args,**kwds):
        """Makes a preview request with a callback function."""
        prog_func = kwds.get("progress_func", None)
        if not prog_func:
            raise KeyError("You must specify a progress function")
        kwds["progress_func"] = self.prog_wrapper(prog_func, "previewflag")
        kwds["renderer"] = config["renderer"]
        self.previewflag = 1

        # This is an append so that a simultaneous request for small and
        # large previews goes through.
##        self.previewqueue = [(callback,metadata,args,kwds)]
        self.previewqueue.append((callback,metadata,args,kwds))


    def RenderRequest(self,callback,metadata,*args,**kwds):
        """Makes a render request run in a different thread than previews,
        so it can be paused."""
        prog_func = kwds.get("progress_func", None)
        if not prog_func:
            raise KeyError("You must specify a progress function")
        kwds["progress_func"] = self.prog_wrapper(prog_func, "bgflag")
        kwds["renderer"] = config["renderer"]

        self.bgqueue = [(callback,metadata,args,kwds)]
        

    @Threaded
    @Catches((TypeError, wx.PyDeadObjectError))
    def RenderLoop(self):
        while not self.exitflag:
            queue = self.previewqueue or self.thumbqueue
            if queue:
                self.previewflag = 0
                callback,metadata,args,kwds = queue.pop(0)

                try:
                    self.bgflag = 2 # Pauses the other thread
                    output_buffer = render(*args,**kwds)
                except Exception:
                    # All exceptions are caught to make sure the render thread
                    # never crashes because of malformed flames.
                    traceback.print_exc()
                    continue
                finally:
                    self.bgflag = 0
                evt = ThreadMessageEvent(callback,metadata,output_buffer)
                wx.PostEvent(self.parent.image,evt)
            else:
                time.sleep(.01)  # Ideal interval needs to be tested


    @Threaded
    @Catches((TypeError, wx.PyDeadObjectError))
    def bgRenderLoop(self):
        while not self.exitflag:
            if self.bgqueue:
                self.previewflag = 0
                callback,metadata,args,kwds = self.bgqueue.pop(0)
                output_buffer = render(*args,**kwds)
                evt = ThreadMessageEvent(callback,metadata,output_buffer)
                wx.PostEvent(self.parent.image,evt)
            else:
                time.sleep(.01)
        

    def prog_wrapper(self, f, flag):
        def prog_func(*args):
            return max(getattr(self, flag), self.exitflag, f(*args))
        return prog_func

    
