import wx

from decorators import *



class PreviewFrame(wx.Frame):
    
    @BindEvents    
    def __init__(self,parent):
        self.title = "Flame Preview"
        self.parent = parent
        wx.Frame.__init__(self,parent,wx.ID_ANY, self.title)
        
        self.image = PreviewPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.image, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self._lastsize = 1,1
        self.SetSize((400,300))


    @Bind(wx.EVT_CLOSE)
    def OnExit(self,e): 
        self.Show(False)
        self.Parent.Raise()


    @Bind(wx.EVT_SIZE)
    def OnResize(self, e):
        size = e.GetSize()
        print size, self._lastsize

        if size == self._lastsize:
            # Don't know why, but each resize triggers 2 events
            return
        
        self._lastsize = size
        self.RenderPreview()

        image = wx.ImageFromBitmap(self.image.bmp)
        pw, ph = map(float,size)
        fw, fh = self.size

        ratio = min(pw/fw, ph/fh)
        image.Rescale(int(fw * ratio), int(fh * ratio))
        self.image.bmp = wx.BitmapFromImage(image)

        self.Refresh()
        e.Skip()


    def RenderPreview(self, flame=None):
        flame = flame or self.parent.flame

        fw,fh = flame.size
        pw,ph = self.GetSize()
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
        self.image.Refresh()

    def prog_func(self, py_object, fraction, stage, eta):
        pass
        

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
        pw,ph = self.parent.GetSize()
        dc.DrawBitmap(self.bmp, (pw-fw)/2, (ph-fh)/2, True)
        

        
