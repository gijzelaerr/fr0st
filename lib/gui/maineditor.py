import wx, itertools
from wx.lib import buttons

from lib.decorators import *
from lib.gui.canvas import XformCanvas
from lib.gui.utils import LoadIcon, MultiSliderMixin, Box, NumberTextCtrl
from lib.gui.config import config


class MainNotebook(wx.Notebook):

    def __init__(self, parent):
        self.parent = parent
        # 390 is just the right width for the gradient to be entirely visible.
        wx.Notebook.__init__(self, parent, -1, size=(390,1), style=
                             wx.BK_DEFAULT
                             )

        transform = TransformPanel(self)
        self.canvas = transform.canvas
        self.AddPage(transform, "Transform Editor")
        
        self.grad = GradientPanel(self)
        self.AddPage(self.grad, "Gradient Editor")

        self.adjust = AdjustPanel(self)
        self.AddPage(self.adjust, "Adjust")


    def UpdateView(self, rezoom=False):
        for i in self.grad, self.adjust:
            i.UpdateView()
        self.canvas.ShowFlame(rezoom=rezoom)



class TransformPanel(wx.Panel):
    
    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        wx.Panel.__init__(self,parent,-1)
        self.toolbar = self.AddFakeToolbar()
        self.canvas = XformCanvas(self)
        
        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(self.toolbar)
        szr.Add(self.canvas, 1, wx.EXPAND)
        
        self.SetSizer(szr)
        self.Layout()

        
    def AddFakeToolbar(self):
        btn = [wx.BitmapButton(self, -1, LoadIcon('toolbar',i),
                                       name=i.replace("-",""),
                                       style=wx.BORDER_NONE)
               for i in ('Clear-Flame',
                         'Add-Xform',
                         'Add-Final-Xform',
                         'Duplicate-Xform',
                         'Delete-Xform')]

        # Add toggle buttons
        # TODO: Isn't there a default Bitmap/Toggle button? Don't like these.
        for i in ('World-Pivot','Lock-Axes','Variation-Preview',
                  'Edit-Post-Xform'):
            b = buttons.GenBitmapToggleButton(self, -1, LoadIcon('toolbar',i),
                                              name=i.replace("-",""),
                                              style=wx.BORDER_NONE)
            b.SetToggle(config[i])
            self.MakeConfigFunc(i)
            btn.append(b)

        szr = wx.BoxSizer(wx.HORIZONTAL)
        szr.AddMany(btn)
        return szr


    def MakeConfigFunc(self, i):
        def onbtn():
            config[i] = not config[i]
            self.parent.canvas.ShowFlame(rezoom=False)
        setattr(self, "Func%s" %i.replace("-",""), onbtn)        


    @Bind(wx.EVT_BUTTON)
    def OnButton(self, e):
        getattr(self, "Func%s" %e.GetEventObject().GetName())()


    def modifyxform(f):
        """This decorator wraps away common code in the button functions."""
        def inner(self):
            # TODO: does this pass post-xforms correctly?
            f(self, self.parent.ActiveXform)
            self.parent.TreePanel.TempSave()
        return inner

    @modifyxform
    def FuncClearFlame(self, xform):
        self.parent.flame.clear()
        self.parent.ActiveXform = self.parent.flame.add_xform()
        
    @modifyxform        
    def FuncAddXform(self, xform):
        self.parent.ActiveXform = self.parent.flame.add_xform()
        
    @modifyxform        
    def FuncAddFinalXform(self, xform):
        # create_final already checks if a final xform exists.
        self.parent.ActiveXform = self.parent.flame.create_final()
        
    @modifyxform           
    def FuncDuplicateXform(self, xform):
        self.parent.ActiveXform = xform.copy()
        
    @modifyxform           
    def FuncDeleteXform(self, xform):
        if not xform.isfinal() and len(xform._parent.xform) == 1:
            # Can't delete the last xform.
            return
        xform.delete()
        self.parent.ActiveXform = None
        

class GradientPanel(wx.Panel):
    _new = None
    _changed = False
    _startval = None
    _flame = None # Only used to check identity
    
    @BindEvents
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1)
        self.parent = parent.parent

        self.config = config["Gradient-Settings"]
        self.dict = {}
        
        choicelist = [('rotate', (-128, 128)),
                      ('hue',(-180,180)),
                      ('saturation', (-100,100)),
                      ('brightness', (-100,100))]
                      ##('blur', (0, 127))]
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
##                                |wx.SL_AUTOTICKS
                                |wx.SL_LABELS)
        self.slider.Bind(wx.EVT_SLIDER, self.OnSlider)
        self.slider.Bind(wx.EVT_LEFT_DOWN, self.OnSliderDown)
        self.slider.Bind(wx.EVT_LEFT_UP, self.OnSliderUp)

        opts = self.MakeTCs("hue", "saturation", "value", "nodes",
                            low=0, high=1, callback=self.OptCallback)
        for i in self.dict["nodes"]:
            i.MakeIntOnly()
            i.SetAllowedRange(1,256)
        btn = wx.Button(self, -1, "Randomize")
        opts = Box(self, "Gradient Generation", opts, btn,
                   orient=wx.HORIZONTAL)
            
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.image,0, wx.EXPAND)
        sizer1.Add(self.Selector,0)
        sizer1.Add(self.slider,0,wx.EXPAND)
        sizer1.Add(opts, 0, wx.EXPAND)
        
        self.SetSizer(sizer1)
        self.Layout()


    def MakeTCs(self, *a, **k):
        fgs = wx.FlexGridSizer(99, 3, 1, 1)
        fgs.AddMany(((0,0),
                     (wx.StaticText(self, -1, "Min"), 0, wx.ALIGN_CENTER),
                     (wx.StaticText(self, -1, "Max"), 0, wx.ALIGN_CENTER)))
        for i in a:
            tc1 = NumberTextCtrl(self, **k)
            tc2 = NumberTextCtrl(self, **k)
            tcs = (tc1, tc2)
            map(NumberTextCtrl.SetFloat, tcs, self.config[i])
            self.dict[i] = tcs
            fgs.Add(wx.StaticText(self, -1, i.replace("_", " ").title()),
                    0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            fgs.Add(tc1, 0, wx.ALIGN_LEFT, 5)
            fgs.Add(tc2, 0, wx.ALIGN_LEFT, 5)
	return fgs


    def UpdateView(self):
        self.image.Update()
        if self.parent.flame != self._flame:
            # Hack: only change the slider when the flame object id changes.
            self.ResetSlider()
            self._flame = self.parent.flame


    def OptCallback(self, tc):
        for k,v in self.dict.iteritems():
            self.config[k] = tuple(i.GetFloat() for i in v)


    @Bind(wx.EVT_BUTTON)
    def OnButton(self, e):
        self.parent.flame.gradient.random(**self.config)
        self.parent.TreePanel.TempSave()
        

    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        if self._new is not None:

            self.parent.flame.gradient[:] = self._grad_copy
            
            self.func(self._new)
            self._new = None
            self._changed = True

            self.image.Update()
            self.parent.image.RenderPreview()

            # HACK: Updating the color tab without calling SetFlame.
            self.parent.XformTabs.Color.UpdateView()
            

    def OnChoice(self, e):
        self.choice = e.GetString()
        self.ResetSlider()


    def ResetSlider(self):
        self.slider.SetValue(0)
        self.slider.SetRange(*self.choices[self.choice])


    def OnSliderDown(self, e):
        self._grad_copy = self.parent.flame.gradient[:]
        self._startval = self.slider.GetValue()
        e.Skip()
        

    def OnSliderUp(self, e):
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
        buff = self.formatstr % tuple(map(int, grad))
        
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
        self.CaptureMouse()
        self._startpos = e.GetPosition()
        parent = self.GetParent()
        self._oldchoice = parent.choice
        parent.choice = 'rotate'
        parent.OnSliderDown(e)
        

    @Bind(wx.EVT_LEFT_UP)
    def OnLeftUp(self, e):
        self.ReleaseMouse()
        self._startpos = None
        parent = self.GetParent()
        parent.choice = self._oldchoice
        # HACK: Need to keep the slider value intact. In the parent's code,
        # this is handled by e.Skip(), which passes the event on to
        # the slider handler. This hack simulates that behaviour.
        val = parent.slider.GetValue()
        parent.OnSliderUp(e)
        parent.slider.SetValue(val)


    @Bind(wx.EVT_MOTION)
    def OnMove(self, e):
        if self._startpos is not None:
            offset = int((e.GetPosition()[0] - self._startpos[0])/1.5)
            self.GetParent()._new = offset


    @Bind(wx.EVT_LEFT_DCLICK)
    def OnDoubleClick(self, e):
        self.Parent.OnButton(None)
            


class AdjustPanel(MultiSliderMixin, wx.Panel):

    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        super(AdjustPanel, self).__init__(parent, -1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany((self.MakeSlider(*i), 0, wx.EXPAND) for i in
                      (("scale", 25, 1, 100, False),
                       ("x_offset", 0, -5, 5, False),
                       ("y_offset", 0, -5, 5, False),
                       ("rotate", 0, -360, 360, True),
                       ("highlight_power", -1, -1, 5, False)))
        self.SetSizer(sizer)


    def UpdateView(self):
        flame = self.parent.flame
        for name in self.sliders:
            self.UpdateSlider(name, getattr(flame, name))         


    def UpdateXform(self):
        for name, val in self.IterSliders():
            setattr(self.parent.flame, name, val)
        self.UpdateView()
        self.parent.image.RenderPreview()

        
