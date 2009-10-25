import wx, os
from functools import partial

from fr0stlib.decorators import *

def LoadIcon(*path):
    # Check for an icons dir in app base path first for development
    filename = os.path.join(wx.GetApp().AppBaseDir, 'icons', *path) + '.png'

    if not os.path.exists(filename):
        # Not there, check install path
        filename = os.path.join(wx.GetApp().IconsDir, *path) + '.png'

    img = wx.Image(filename, type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16,16)
    return wx.BitmapFromImage(img)


def Box(self, name, *a, **k):
    box = wx.StaticBoxSizer(wx.StaticBox(self, -1, name),
                            k.get('orient', wx.VERTICAL))
    box.AddMany(a)
    return box


def MakeTCs(self, *a, **k):
    fgs = wx.FlexGridSizer(99, 2, 1, 1)
    tcs = {}
    for i, default in a:
        tc = NumberTextCtrl(self, **k)
        tc.SetFloat(default)
        tcs[i] = tc
        fgs.Add(wx.StaticText(self, -1, i.replace("_", " ").title()),
                0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        fgs.Add(tc, 0, wx.ALIGN_RIGHT, 5)
    return fgs, tcs


class MyChoice(wx.Choice):
    def __init__(self, parent, name, d, initial):
        self.d = d
        choices = sorted(d.iteritems())
        wx.Choice.__init__(self, parent, -1, choices=[k for k,_ in choices])
        self.SetSelection([v for _,v in choices].index(initial))


    def GetFloat(self):
        return self.d[self.GetStringSelection()]


class SizePanel(wx.Panel):
    def __init__(self, parent, callback=lambda: None):
        self.parent = parent
        self.keepratio = True
        self.callback = callback
        wx.Panel.__init__(self, parent, -1)

        fgs, tcs = MakeTCs(self, ("width", 512.), ("height", 384.), low=0,
                           callback=self.SizeCallback)
        self.__dict__.update(tcs)
        for i in (self.width, self.height):
            i.MakeIntOnly()
            i.low = 1

        ratio = wx.CheckBox(self, -1, "Keep Ratio")
        ratio.SetValue(True)
        ratio.Bind(wx.EVT_CHECKBOX, self.OnRatio)

        box = Box(self, "Size", fgs, ratio)
        self.SetSizer(box)
        box.Fit(self)
    

    def GetInts(self):
        return [int(tc.GetFloat()) for tc in (self.width, self.height)]


    def UpdateSize(self, size):
        width, height = (float(i) for i in size)
        self.width.SetFloat(width)
        self.height.SetFloat(height)
        self.ratio = width / height


    def OnRatio(self, e):
        self.keepratio = e.GetInt()


    def SizeCallback(self, tc, tempsave=None):
        if self.keepratio:
            v = tc.GetFloat()
            tc.SetInt(v)
            if tc == self.width:
                w, h = v, v / self.ratio
                self.height.SetInt(h)
            else:
                w, h = v * self.ratio, v
                self.width.SetInt(w)
        else:
            self.ratio = float(self.width.GetFloat()) / self.height.GetFloat()
        self.callback()



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
            self.callback = lambda tempsave=None: None

        self.HasChanged = False
        
        self.SetFloat(0.0)
            

    def GetFloat(self):
        return float(self.GetValue() or "0")

    def SetFloat(self, v):
        v = self.Checkrange(float(v))
        self._value = v
        string = ("%.6f" %v).rstrip("0")
        if string.endswith("."):
            string += "0" # Avoid values like '0.' or '1.'
        self.SetValue(string)


    def GetInt(self):
        return int(self.GetValue() or "0")

    def SetInt(self, v):
        v = self.Checkrange(int(v))
        self._value = v
        self.SetValue(str(v))


    def MakeIntOnly(self):
        self.SetInt(self.GetFloat())
        self.SetFloat, self.GetFloat = self.SetInt, self.GetInt
        

    def SetAllowedRange(self, low=None, high=None):
        self.low = low
        self.high = high


    def Checkrange(self, v):
        if self.low is not None and v < self.low:
            return self.low
        elif self.high is not None and v > self.high:
            return self.high
        return v

    @Bind(wx.EVT_MOUSEWHEEL)
    def OnMouseWheel(self, evt):
        if self.SetFloat == self.SetInt:
            return

        if evt.CmdDown():
            if evt.AltDown():
                delta = 0.01
            else:
                delta = 0.1
        elif evt.AltDown():
            delta = 0.001
        else:
            evt.Skip()
            return

        self.SetFocus() # Makes sure OnKeyUp gets called.

        v = self._value + delta * evt.GetWheelRotation() / evt.GetWheelDelta()
        self.SetFloat(v)
        self.callback(tempsave=False)
        self.HasChanged = True

        
    @Bind(wx.EVT_KEY_UP)
    def OnKeyUp(self, e):
        # TODO: This code is duplicated with the one found in xformeditor.
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                if hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'TreePanel'):
                    self.parent.parent.TreePanel.TempSave()
                self.HasChanged = False


    @Bind(wx.EVT_CHAR)
    def OnChar(self, event):
        key = event.GetKeyCode()
        if key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            self.OnKillFocus(None)
        elif key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255 or key == wx.WXK_TAB:
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
            self.SetFloat(v)
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
            self.UpdateFlame()
            self._new = None
            self._changed = True


    def __callback(self, tc, tempsave=True):
        self.UpdateFlame()
        if tempsave:
            self.parent.TreePanel.TempSave()
        

    def UpdateFlame(self):
        Abstract


    def UpdateView(self):
        Abstract
