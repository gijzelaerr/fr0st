import wx

from decorators import *
from lib.functions import flatten
from array import array

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
        new = e.GetInt()
        val = (new - self._old)/180.+0.5
        self._old = new
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
        grad = flatten(flame.gradient)
##        buff = array('c',map(chr,grad))
        buff = self.formatstr % tuple(grad)
        self.bmp = wx.BitmapFromBuffer(256, 50, buff *50)

        self.Refresh()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 2, 0, True)

