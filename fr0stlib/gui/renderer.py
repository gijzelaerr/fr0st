import time, sys, traceback
from collections import defaultdict
from wx import PyDeadObjectError

from fr0stlib.decorators import Catches, Threaded
from fr0stlib.render import flam3_render, flam4_render
from fr0stlib.gui.config import config


class Renderer():
    def __init__(self, parent):
        self.parent = parent
        self.thumbqueue = []
        self.previewqueue = []
        self.largepreviewqueue = []
        self.bgqueue = []
        self.exitflag = 0
        self.previewflag = 0
        self.bgflag = 0
        if "-debug" not in sys.argv:
            # TODO: remove this.
            self.RenderLoop()
            self.bgRenderLoop()


    def ThumbnailRequest(self, callback, *args, **kwds):
        """Schedules a thumbnail to be rendered."""
        # These settings are hardcoded on purpose, they can't be overridden
        # by the calling code.
        kwds["nthreads"] = 1
        kwds["fixed_seed"] = True
        kwds["renderer"] = "flam3"
        
        self.thumbqueue.append((callback,args,kwds))


    def PreviewRequest(self, callback, *args, **kwds):
        """Schedules a render immediately after the current render is done.
        Cancels previous requests (assuming they are obsolete)."""
        kwds["nthreads"] = 1
        kwds["fixed_seed"] = True
        kwds["renderer"] = "flam3"
        self.previewflag = 1
        
        self.previewqueue = [(callback,args,kwds)]

        
    def LargePreviewRequest(self, callback, *args, **kwds):
        """Makes a preview request with a progress function."""
        prog_func = kwds.get("progress_func", None)
        if not prog_func:
            raise KeyError("You must specify a progress function")
        kwds["progress_func"] = self.prog_wrapper(prog_func, "previewflag")
        kwds["renderer"] = kwds.get("renderer", config["renderer"])
        self.previewflag = 1

        self.largepreviewqueue = [(callback,args,kwds)]


    def RenderRequest(self, callback, *args, **kwds):
        """Makes a render request run in a different thread than previews,
        so it can be paused."""
        prog_func = kwds.get("progress_func", None)
        if not prog_func:
            raise KeyError("You must specify a progress function")
        kwds["progress_func"] = self.prog_wrapper(prog_func, "bgflag")
        kwds["renderer"] = kwds.get("renderer", config["renderer"])

        self.bgqueue.append((callback,args,kwds))
        

    @Threaded
    def RenderLoop(self):
        while not self.exitflag:
            queue = (self.previewqueue or self.thumbqueue 
                     or self.largepreviewqueue)
            if queue:
                self.bgflag = 2 # Pauses the other thread
                self.previewflag = 0
                self.process(*queue.pop(0))
                self.bgflag = 0
            else:
                time.sleep(.01)  # Ideal interval needs to be tested


    @Threaded
    def bgRenderLoop(self):
        while not self.exitflag:
            queue = self.bgqueue
            if queue:
                self.process(*queue.pop(0))
            else:
                time.sleep(.01)


    @Catches(PyDeadObjectError)
    def process(self, callback, args, kwds):
        renderer = kwds.pop("renderer")
        if renderer == "flam3":
            render = flam3_render
        elif renderer == "flam4":
            render = flam4_render
        else:
            raise ValueError("Invalid renderer: %s" % renderer)
        try:
            output_buffer = render(*args,**kwds)
        except Exception:
            # Make sure render thread never crashes due to malformed flames.
            traceback.print_exc()
            return

        # HACK: If by the time the render finishes it has been obsoleted,
        # don't return the buffer in case of a large preview.
        if hasattr(callback, "_can_cancel") and self.previewflag:
            return        
        
        if renderer == 'flam4':
            channels = 4
        else:
            channels = kwds.get('transparent', False) + 3
        # args[1] is always size...
        self.parent.OnImageReady(callback, args[1], output_buffer, channels)
        

    def prog_wrapper(self, f, flag):
        @Catches(TypeError)
        def prog_func(*args):
            return self.exitflag or f(*args) or getattr(self, flag)
        return prog_func

    
