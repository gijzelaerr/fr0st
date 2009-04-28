import wx, sys

from decorators import *
from _events import EVT_PROGRESS, ProgressEvent



class PreviewFrame(wx.Frame):
    
    @BindEvents    
    def __init__(self,parent):
        self.title = "Flame Preview"
        self.parent = parent
        wx.Frame.__init__(self,parent,wx.ID_ANY, self.title)

        self.CreateStatusBar()
        
        self.image = PreviewPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.image, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetDoubleBuffered(True)
        self.oldbmp = None

        self._lastsize = 1,1
        self.SetSize((600,450))
        self.SetMinSize((128,119)) # This makes for a 120x90 bitmap

    def GetCorrectSize(self):
        """This method corrects platform dependency issues."""
        if "linux" in sys.platform:
            return self.GetSize()
        return self.GetCorrectSize()


    @Bind(wx.EVT_CLOSE)
    def OnExit(self,e): 
        self.Show(False)
        self.Parent.Raise()


##    @Bind(wx.EVT_SIZE if "linux" in sys.platform else wx.EVT_IDLE)
    @Bind(wx.EVT_SIZE)
    def OnResize(self, e):
        size = self.GetCorrectSize() # e.GetSize()

        if not self.oldbmp:
            self.oldbmp = self.image.bmp
        image = wx.ImageFromBitmap(self.oldbmp)

        pw, ph = map(float,size)
        fw, fh = self.image.bmp.GetSize() # This used to be self.size (?)

        ratio = min(pw/fw, ph/fh)
        image.Rescale(int(fw * ratio), int(fh * ratio))
        self.image.bmp = wx.BitmapFromImage(image)

        self.Refresh()
        e.Skip()


    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        size = self.GetCorrectSize()
        if size == self._lastsize:
            return

        self._lastsize = size
        self.RenderPreview()
        

    def RenderPreview(self, flame=None):
        flame = flame or self.parent.flame

        fw,fh = flame.size
        pw,ph = self.GetCorrectSize()
        ratio = min(pw/fw, ph/fh)
        size = int(fw * ratio), int(fh * ratio)
        self.size = size
        
        req = self.parent.renderer.LargePreviewRequest
        req(self.UpdateBitmap,size,flame.to_string(),
            size,quality=10,estimator=0,filter=.2,
            progress_func = self.prog_func)


    def UpdateBitmap(self,size,output_buffer):
        """Callback function to process rendered preview images."""
        width,height = size
        self.image.bmp = wx.BitmapFromBuffer(width, height, output_buffer)
        self.SetTitle("%s - Flame Preview" % self.parent.flame.name)
        self.SetStatusText("rendering: 100.00 %")
        self.image.Refresh()
        self.oldbmp = None


    def prog_func(self, *args):
        wx.PostEvent(self, ProgressEvent(*args))


    @Bind(EVT_PROGRESS)
    def OnProgress(self, e):
        py_object, fraction, stage, eta = e.GetArgs()
        self.SetStatusText("rendering: %.2f %%" %fraction)
        

class PreviewPanel(wx.Panel):

    @BindEvents    
    def __init__(self,parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.bmp = wx.EmptyBitmap(400,300, 32)


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):       
        fw,fh = self.bmp.GetSize()
        dc = wx.PaintDC(self)
        pw,ph = self.parent.GetCorrectSize()
        dc.DrawBitmap(self.bmp, (pw-fw)/2, (ph-fh)/2, True)
        

        
