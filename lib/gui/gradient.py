import wx, itertools

from decorators import *

from lib.gui.canvas import XformCanvas


# TODO: this class doesn't belong here.
class MainNotebook(wx.Notebook):

    def __init__(self, parent):
        self.parent = parent
        # 390 is just the right width for the gradient to be entirely visible.
        wx.Notebook.__init__(self, parent, -1, size=(390,1), style=
                             wx.BK_DEFAULT
                             )

        self.canvas = XformCanvas(self)
        self.AddPage(self.canvas, "Transform Editor")
        
        self.grad = GradientPanel(self)
        self.AddPage(self.grad, "Gradient Editor")



class GradientPanel(wx.Panel):

    @BindEvents
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1)
        self.parent = parent.parent
##        self._old = 0
        self._new = None
        self._changed = False
        
        choicelist = [('rotate', (-128, 128)),
                      ('hue',(-180,180)),
                      ('saturation', (-100,100)),
                      ('brightness', (-100,100)),
                      ('blur', (0, 127))]
        self.choices = dict(choicelist)
        self.choice = 'rotate'
        self.func = lambda x: getattr(self.parent.flame.gradient,
                                      self.choice)(x)

        #Gradient image
        self.image = Gradient(self)
        #Controls - choice for method and slider
        self.Selector = wx.Choice(self, -1, choices=[i[0] for i in choicelist])
        self.Selector.Bind(wx.EVT_CHOICE, self.OnChoice)
        
        self.slider = wx.Slider(self, -1, 0, -180, 180,
                                style=wx.SL_HORIZONTAL
                                |wx.SL_AUTOTICKS
                                |wx.SL_LABELS)
        self.slider.Bind(wx.EVT_SLIDER, self.OnSlider)
        self.slider.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.slider.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
            
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.image,0, wx.EXPAND)
        sizer1.Add(self.Selector,0)
        sizer1.Add(self.slider,0,wx.EXPAND)
        
        self.SetSizer(sizer1)
        self.Layout()

        self._startval = None


    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        if self._new is not None:
##            val = (self._new - self._old)
##            self._old, self._new = self._new, None

            self.parent.flame.gradient[:] = self._grad_copy
            
            self.func(self._new)
            self._new = None
            self._changed = True

            self.image.Update()
            self.parent.image.RenderPreview()
        

    def OnChoice(self, e):
        self.choice = e.GetString()
        self.ResetSlider()


    def ResetSlider(self):
        self.slider.SetValue(0)
        self.slider.SetRange(*self.choices[self.choice])


    def OnLeftDown(self, e):
        self._grad_copy = self.parent.flame.gradient[:]
        self._startval = self.slider.GetValue()
        e.Skip()
        

    def OnLeftUp(self, e):
        if self._changed:
            self.parent.TreePanel.TempSave()
            self._changed = False
        self._startval = None
        e.Skip()

        
    def OnSlider(self, e):
        if self._startval is not None:
            self._new = e.GetInt() - self._startval

        

class Gradient(wx.Panel):
    formatstr = "%c" * 256 * 3

    @BindEvents
    def __init__(self,parent):
        self.parent = parent.parent
        wx.Panel.__init__(self, parent, -1)
        self.bmp = wx.EmptyBitmap(1,1,32)
        self.SetMinSize((390,60))
        self._startpos = None

    def Update(self, flame=None):
        flame = flame or self.parent.flame

        grad = itertools.chain(*flame.gradient)
        buff = self.formatstr % tuple(grad)
        
##        self.bmp = wx.BitmapFromBuffer(256, 50, buff *50)
        img = wx.ImageFromBuffer(256, 1, buff)
        img.Rescale(384, 50)
        self.bmp = wx.BitmapFromImage(img)

        self.Refresh()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 2, 2, True)

    
    @Bind(wx.EVT_LEFT_DOWN)
    def OnLeftDown(self, e):
        self._startpos = e.GetPosition()
        parent = self.GetParent()
        self._oldchoice = parent.choice
        parent.choice = 'rotate'
        parent.OnLeftDown(e)
        

    @Bind(wx.EVT_LEFT_UP)
    def OnLeftUp(self, e):
        self._startpos = None
        parent = self.GetParent()
        parent.choice = self._oldchoice
        # HACK: Need to keep the slider value intact. In the parent's code,
        # this is handled by e.Skip(), which passes the event on to
        # the slider handler. This hack simulates that behaviour.
        val = parent.slider.GetValue()
        parent.OnLeftUp(e)
        parent.slider.SetValue(val)


    @Bind(wx.EVT_MOTION)
    def OnMove(self, e):
        if self._startpos is not None:
            offset = int((e.GetPosition()[0] - self._startpos[0])/1.5)
            self.GetParent()._new = offset
            
            
