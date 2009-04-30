import wx, itertools

from decorators import *

from lib.gui.canvas import XformCanvas


# TODO: this class doesn't belong here.
class MainNotebook(wx.Notebook):

    def __init__(self, parent):
        self.parent = parent
        wx.Notebook.__init__(self, parent, -1, size=(21,21), style=
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
        self.choice = 'rotate'
        self._old = 0
        self._new = None
        
        self.choices = {'hue':(-180,180),
                        'saturation': (-100,100),
                        'brightness': (-100,100),
                        'blur': (0, 127),
                        'rotate': (-128, 128)}
        self.choice = 'rotate'
        self.func = lambda x: getattr(self.parent.flame.gradient,
                                      self.choice)(x)

        #Gradient image
        self.image = Gradient(self)
        #Controls - choice for method and slider
        self.Selector = wx.Choice(self, -1, choices=self.choices.keys())
        self.Selector.Bind(wx.EVT_CHOICE, self.OnChoice)
        
        self.slider = wx.Slider(self, -1, 0, -180, 180,
                                style=wx.SL_HORIZONTAL
                                |wx.SL_AUTOTICKS
                                |wx.SL_LABELS)
        self.slider.Bind(wx.EVT_SLIDER,self.OnSlider)
            
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.image,0, wx.EXPAND)
        sizer1.Add(self.Selector,0)
        sizer1.Add(self.slider,0,wx.EXPAND)
        
        self.SetSizer(sizer1)
        self.Layout()


    def OnSlider(self, e):
        self._new = e.GetInt()
##        val = (new - self._old)
##        self._old = new
##        self.func(val)
##        self.image.Update()


    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        if self._new is not None:
            val = (self._new - self._old)
            self._old, self._new = self._new, None
            self.func(val)
            self.image.Update()            
        

    def OnChoice(self, e):
        self.choice = e.GetString()
##        for i in dir(self.slider):
##            print i
        self.slider.SetValue(0)
        self.slider.SetRange(*self.choices[self.choice])

    # TODO: onleftup needs to trigger a tempsave
    # also implement gradient dragging here



class Gradient(wx.Panel):
    formatstr = "%c" * 256 * 3

    @BindEvents
    def __init__(self,parent):
        self.parent = parent.parent
        wx.Panel.__init__(self, parent, -1, size=wx.Size(260, 30))
        self.bmp = wx.EmptyBitmap(256,50,32)


    def Update(self, flame=None):
        flame = flame or self.parent.flame

        grad = itertools.chain(*flame.gradient)
        buff = self.formatstr % tuple(grad)
        
##        self.bmp = wx.BitmapFromBuffer(256, 50, buff *50)
        img = wx.ImageFromBuffer(256, 1, buff)
        img.Rescale(256, 50)
        self.bmp = wx.BitmapFromImage(img)

        self.Refresh()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 2, 0, True)

    @Bind(wx.EVT_LEFT_DOWN)
    def OnLeftDown(self, e):
        self._grad_copy = self.parent.flame.gradient[:]
        self._startpos = e.GetPosition()

    @Bind(wx.EVT_LEFT_UP)
    def OnLeftUp(self, e):
        self.parent.TreePanel.TempSave()

    @Bind(wx.EVT_MOVE)
    def OnMove(self, e):
        if e.LeftIsDown() and e.Dragging():
            offset = e.GetPosition[0] - self._startpos[0]
            
            
