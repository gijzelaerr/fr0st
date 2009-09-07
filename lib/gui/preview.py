import wx, sys, numpy as N

from lib.decorators import *
from config import config
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

        # This must be 0,0 so OnIdle doesn't render anything on startup.
        self._lastsize = 0,0
        
        self.SetSize((520,413))
        self.SetMinSize((128,119)) # This makes for a 120x90 bitmap


    def GetPanelSize(self):
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
        if not self.image.oldbmp:
            self.image.oldbmp = self.image.bmp
        image = wx.ImageFromBitmap(self.image.oldbmp)


        # TODO: This was here for windows. Need to find a clean way to make
        # resize work nice and consistent cross-platform.
##        if self._lastsize == (0,0):
##            return
        
        pw, ph = map(float, self.GetPanelSize())
        fw, fh = self.parent.flame.size

        ratio = min(pw/fw, ph/fh)
        image.Rescale(int(fw * ratio), int(fh * ratio))
        self.image.bmp = wx.BitmapFromImage(image)

        self.Refresh()
        e.Skip()


    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        size = self.GetPanelSize()
        if size == self._lastsize:
            return

        self._lastsize = size
        self.RenderPreview()
        

    def RenderPreview(self, flame=None):
        flame = flame or self.parent.flame

        fw,fh = flame.size
        pw,ph = self.GetPanelSize()

        ratio = min(pw/fw, ph/fh)
        size = int(fw * ratio), int(fh * ratio)
        
        req = self.parent.renderer.LargePreviewRequest
        req(self.RenderCallback, flame, size, progress_func=self.prog_func,
            **config["Large-Preview-Settings"])


    def RenderCallback(self, bmp):
        self.image.UpdateBitmap(bmp)
        self.SetTitle("%s - Flame Preview" % self.parent.flame.name)
        self.SetStatusText("rendering: 100.00 %")

    RenderCallback._can_cancel = True


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
        flame.move_center([i / pixel_per_unit for i in diff])
        self.parent.image.RenderPreview()
        self.parent.adjust.UpdateView()


    def Zoom(self, diff):
        self.parent.flame.scale *= diff
        self.parent.image.RenderPreview()
        self.parent.adjust.UpdateView()
        self.HasChanged = True       


    @Bind(wx.EVT_LEFT_DOWN)
    def OnLeftDown(self, e):
        self.SetFocus()
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
    _offset = N.array([0,0])
    _zoomfactor = 1.0
    oldbmp = None

    @BindEvents
    def __init__(self, parent):
        self.__class__ = PreviewBase
        PreviewBase.__init__(self, parent)
        self.__class__ = PreviewPanel
        self.parent = parent.parent
        self.GetPanelSize = parent.GetPanelSize       


    def UpdateBitmap(self, bmp):
        self.bmp = bmp
        self.oldbmp = bmp
        self._offset = N.array([0,0])
        self._zoomfactor = 1.0
        self.Refresh()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):       
        fw,fh = self.bmp.GetSize()
        pw,ph = self.GetPanelSize()
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, (pw-fw)/2, (ph-fh)/2, True)
        

    def Move(self, diff):
        PreviewBase.Move(self, diff)
        self._offset += diff
        self.MoveAndZoom()
        

    def Zoom(self, val):
        PreviewBase.Zoom(self, val)
        self._zoomfactor *= val        
        self._offset *= val
        self.MoveAndZoom()
        

    def MoveAndZoom(self):
        fw,fh = self.bmp.GetSize()
        ow, oh = self._offset
        image = wx.ImageFromBitmap(self.oldbmp)

        # Use fastest order of operations in each case (i.e. the order that
        # avoids huge images that will just be shrinked or cropped).
        # Both paths yield equivalent results.
        zoom = self._zoomfactor
        if zoom > 1:
            iw, ih = int(fw/zoom), int(fh/zoom)
            newimg = wx.EmptyImage(iw, ih, 32)
            newimg.Paste(image, (iw-fw)/2 - ow/zoom,
                                (ih-fh)/2 - oh/zoom)
            newimg.Rescale(fw,fh)
        else:
            iw, ih = int(fw*zoom), int(fh*zoom)
            image.Rescale(iw, ih)
            newimg = wx.EmptyImage(fw, fh, 32)
            newimg.Paste(image, (fw-iw)/2 - ow, (fh-ih)/2 - oh)

        self.bmp = wx.BitmapFromImage(newimg)
        self.Refresh()        
