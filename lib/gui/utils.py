import wx, os, functools

from lib.decorators import *

def LoadIcon(*path):
    img = wx.Image(os.path.join('lib','gui','icons',*path) + '.png',
                                type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16,16)
    return wx.BitmapFromImage(img)



class NumberTextCtrl(wx.TextCtrl):
    low = None
    high = None

    @BindEvents
    def __init__(self, parent):
        self.parent = parent
        # Size is set to ubuntu default (75,27), maybe make it 75x21 in win
        wx.TextCtrl.__init__(self,parent,-1, size=(75,27))
        self.SetValue("0.0")
        self._value = 0.0

    def GetFloat(self):
        return float(self.GetValue() or "0")

    def SetFloat(self,v):
        # Make sure pure ints don't make trouble
        v = float(v)
        self._value = v
        if abs(v) < 1E-06:
            string = "0.0" # Avoids a value of "0." 
        else:
            string = ("%.6f" %v).rstrip("0")
            
        self.SetValue(string)


    def SetAllowedRange(self, low=None, high=None):
        self.low = low
        self.high = high


    @Bind(wx.EVT_CHAR)
    def OnChar(self, event):
        key = event.GetKeyCode()
        if key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            self.OnKillFocus(None)
        elif key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
        elif chr(key) in "0123456789.-":
            event.Skip()  
        else:
            # not calling Skip() eats the event
            pass #wx.Bell()


    @Bind(wx.EVT_KILL_FOCUS)
    def OnKillFocus(self,event):
        # cmp done with strings because equal floats can compare differently.
        if str(self._value) != self.GetValue():
            try:
                v = self.GetFloat() # Can raise ValueError
                if self.low is not None and v < self.low:
                    raise ValueError
                if self.high is not None and v > self.high:
                    raise ValueError
                self._value = v
                self.parent.UpdateXform()
            except ValueError:
                self.SetFloat(self._value)
        


class MultiSliderMixin(object):
    """Class to dynamically create and control sliders."""
    _new = None

    def __init__(self, *a, **k):
        super(MultiSliderMixin, self).__init__(*a, **k)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

    
    def MakeSlider(self, name, init=0, low=0, high=100):
        """Programatically builds stuff."""
        slider = wx.Slider(self, -1, init, low, high,
                           style=wx.SL_HORIZONTAL
                           |wx.SL_LABELS)
        tc = NumberTextCtrl(self)
        tc.SetAllowedRange(low/100., high/100.)
        setattr(self, "%sslider" %name, slider)
        setattr(self, "%stc" %name, tc)

        slider.Bind(wx.EVT_SLIDER, functools.partial(self.OnSlider, name=name))
##        slider.Bind(wx.EVT_LEFT_DOWN, self.OnSliderDown)
        slider.Bind(wx.EVT_LEFT_UP, self.OnSliderUp)

        siz = wx.StaticBoxSizer(wx.StaticBox(self, -1, name), wx.HORIZONTAL)
        siz.Add(tc)
        siz.Add(slider, wx.EXPAND)

        return siz


    def OnSlider(self, e, name):
        val = e.GetInt()/100.
        tc = getattr(self, "%stc" %name)
        # Make sure _new is only set when there are actual changes.
        if val != tc._value:
            self._new = True
            tc.SetFloat(str(val))
        e.Skip()

     
##    def OnSliderDown(self, e):
##        e.Skip()


    def OnSliderUp(self, e):
        if self._changed:
            self.parent.TreePanel.TempSave()
            self._changed = False
        e.Skip()


    def OnIdle(self, e):
        if self._new is not None:
            self.UpdateXform()
            self._new = None
            self._changed = True


    def UpdateXform(self):
        Abstract


    def UpdateView(self):
        Abstract
