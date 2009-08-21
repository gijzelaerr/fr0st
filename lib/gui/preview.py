import wx, sys, numpy as N

from lib.decorators import *
from _events import EVT_THREAD_MESSAGE, ThreadMessageEvent


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

        # This must be 0,0 so OnIdle doesn't render anything on startup.
        self._lastsize = 0,0
        
        self.SetSize((520,413))
        self.SetMinSize((128,119)) # This makes for a 120x90 bitmap


    def GetCorrectSize(self):
        """This method corrects platform dependency issues."""
##        if "linux" in sys.platform:
##            return self.GetSize()
        return self.GetSizer().GetSize()


    @Bind(wx.EVT_CLOSE)
    def OnExit(self,e): 
        self.Show(False)
        self.Parent.Raise()


    @Bind(wx.EVT_SIZE)
    def OnResize(self, e):
        if not self.oldbmp:
            self.oldbmp = self.image.bmp
        image = wx.ImageFromBitmap(self.oldbmp)

        pw, ph = map(float, self.GetCorrectSize())
        fw, fh = self.parent.flame.size

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
        
        req = self.parent.renderer.LargePreviewRequest
        req(self.UpdateBitmap, flame, size, quality=10, estimator=0, filter=.2,
            progress_func = self.prog_func)


    def UpdateBitmap(self, bmp):
        """Callback function to process rendered preview images."""
        self.image.bmp = bmp
        self.SetTitle("%s - Flame Preview" % self.parent.flame.name)
        self.SetStatusText("rendering: 100.00 %")
        self.image.Refresh()
        self.oldbmp = None


    def prog_func(self, *args):
        wx.PostEvent(self, ThreadMessageEvent(-1, *args))


    @Bind(EVT_THREAD_MESSAGE)
    def OnProgress(self, e):
        py_object, fraction, stage, eta = e.GetArgs()
        self.SetStatusText("rendering: %.2f %%" %fraction)


        
class PreviewBase(wx.Panel):
    HasChanged = False
    StartMove = None
    EndMove = None
    _move = None
    _zoom = 1


    @BindEvents
    def __init__(self, parent):
        self.bmp = wx.EmptyBitmap(400,300, 32)
        wx.Panel.__init__(self, parent, -1)
        

    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        if self._move is not None:
            diff = self._move
            self._move = None
            self.StartMove = self.EndMove
            self.Move(diff)
        elif self._zoom != 1:
            diff = self._zoom
            self._zoom = 1
            self.Zoom(diff)
            

    def Move(self, diff):
            flame = self.parent.flame
            fw,fh = self.bmp.GetSize()
            pixel_per_unit = fw * flame.scale / 100.
            print diff, pixel_per_unit
            flame.center[0] += diff[0] / pixel_per_unit
            flame.center[1] += diff[1] / pixel_per_unit
            self.parent.image.RenderPreview()


    def Zoom(self, diff):
        self.parent.flame.scale *= diff
        self.parent.image.RenderPreview()
        self.HasChanged = True       


    @Bind(wx.EVT_LEFT_DOWN)
    def OnLeftDown(self, e):
        self.StartMove = N.array(e.GetPosition())


    @Bind(wx.EVT_LEFT_UP)
    def OnLeftUp(self, e):
        self.StartMove = None
        if self.EndMove is not None:
            self.EndMove = None
            self.parent.TreePanel.TempSave()


    @Bind(wx.EVT_MOUSE_EVENTS)
    def OnMove(self, e):
        if self.StartMove is not None:
            self.EndMove = N.array(e.GetPosition())
            self._move = self.StartMove - self.EndMove

        
    @Bind(wx.EVT_MOUSEWHEEL)
    def OnWheel(self, e):
        if e.ControlDown():
            if e.AltDown():
                diff = 0.01
            else:
                diff = 0.1
        elif e.AltDown():
            diff = 0.001
        else:
            e.Skip()
            return

        self.SetFocus() # Makes sure OnKeyUp gets called.

        self._zoom *= 1 + (diff if e.GetWheelRotation() > 0 else -diff)
         

    @Bind(wx.EVT_KEY_UP)
    def OnKeyUp(self, e):
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TreePanel.TempSave()
                self.HasChanged = False
   


class PreviewPanel(PreviewBase):

    @BindEvents
    def __init__(self, parent):
        self.__class__ = PreviewBase
        PreviewBase.__init__(self, parent)
        self.__class__ = PreviewPanel
        self.parent = parent.parent
        self.GetCorrectSize = parent.GetCorrectSize       
        

    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):       
        fw,fh = self.bmp.GetSize()
        dc = wx.PaintDC(self)
        pw,ph = self.GetCorrectSize()
        dc.DrawBitmap(self.bmp, (pw-fw)/2, (ph-fh)/2, True)


    def Move(self, diff):
        PreviewBase.Move(self, diff)
        # TODO: Move bitmap


    def Zoom(self, val):
        PreviewBase.Zoom(self, val)
        # TODO: Zoom bmp
