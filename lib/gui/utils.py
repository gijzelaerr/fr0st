import wx, os
from functools import partial

from lib.decorators import *

def LoadIcon(*path):
    img = wx.Image(os.path.join('lib','gui','icons',*path) + '.png',
                                type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16,16)
    return wx.BitmapFromImage(img)


def Box(self, name, *a, **k):
    box = wx.StaticBoxSizer(wx.StaticBox(self, -1, name),
                            k.get('orient', wx.VERTICAL))
    box.AddMany(a)
    return box



class MyChoice(wx.Choice):
    def __init__(self, parent, name, d, initial):
        self.d = d
        choices = sorted(d.iteritems())
        wx.Choice.__init__(self, parent, -1, choices=[k for k,_ in choices])
        self.SetSelection([v for _,v in choices].index(initial))


    def GetFloat(self):
        return self.d[self.GetStringSelection()]

    

class NumberTextCtrl(wx.TextCtrl):
    low = None
    high = None

    @BindEvents
    def __init__(self, parent, low=None, high=None, callback=None):
        self.parent = parent
        # Size is set to ubuntu default (75,27), maybe make it 75x21 in win
        wx.TextCtrl.__init__(self,parent,-1, size=(75,27))
        
        if (low,high) != (None,None):
            self.SetAllowedRange(low, high)

        if callback:
            self.callback = partial(callback, self)
        else:
            self.callback = lambda: None
    
        self.SetFloat(0.0)
            

    def GetFloat(self):
        return float(self.GetValue() or "0")

    def SetFloat(self, v):
        v = float(v)
        self._value = v
        string = ("%.6f" %v).rstrip("0")
        if string.endswith("."):
            string += "0" # Avoid values like '0.' or '1.'
        self.SetValue(string)


    def GetInt(self):
        return int(self.GetValue() or "0")

    def SetInt(self, v):
        v  = int(v)
        self._value = v
        self.SetValue(str(v))


    def MakeIntOnly(self):
        self.SetInt(self.GetFloat())
        self.SetFloat, self.GetFloat = self.SetInt, self.GetInt
        

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
            except ValueError:
                self.SetFloat(self._value)
                return
            if self.low is not None and v < self.low:
                self.SetFloat(self.low)
                return
            elif self.high is not None and v > self.high:
                self.SetFloat(self.high)
                return
            self._value = v
            self.callback()
        


class MultiSliderMixin(object):
    """Class to dynamically create and control sliders."""
    _new = None
    _changed = False

    def __init__(self, *a, **k):
        super(MultiSliderMixin, self).__init__(*a, **k)
        self.sliders = {}
        self.Bind(wx.EVT_IDLE, self.OnIdle)


    def MakeSlider(self, name, init, low, high, strictrange=True):
        """Programatically builds stuff."""
        slider = wx.Slider(self, -1, init*100, low*100, high*100,
                           style=wx.SL_HORIZONTAL
                           | wx.SL_SELRANGE
                           )
        tc = NumberTextCtrl(self, callback=self.__callback)
        if strictrange:
            tc.SetAllowedRange(low, high)
        self.sliders[name] = slider, tc

        slider.Bind(wx.EVT_SLIDER, partial(self.OnSlider, tc=tc))
##        slider.Bind(wx.EVT_LEFT_DOWN, self.OnSliderDown)
        slider.Bind(wx.EVT_LEFT_UP, self.OnSliderUp)

        name = name.replace("_", " ").title()
        return Box(self, name, tc, (slider, wx.EXPAND), orient=wx.HORIZONTAL)


    def UpdateSlider(self, name, val):
        slider, tc = self.sliders[name]
        slider.SetValue(int(val*100))
        tc.SetFloat(val)         


    def IterSliders(self):
        for name, (_, tc) in self.sliders.iteritems():
            yield name, tc.GetFloat()

    
    def OnSlider(self, e, tc):
        val = e.GetInt()/100.
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


    def __callback(self, tc):
        self.UpdateXform()
        self.parent.TreePanel.TempSave()
        

    def UpdateXform(self):
        Abstract


    def UpdateView(self):
        Abstract
