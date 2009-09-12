#Render Dialog Script for Fr0st
#(Re)Started by Brad on April 6th at 8:00 pm.
#Designed to be a basic dialog that will render the current flame to an image file.
#Changelog:
#   Started April 6th.
#   Basic Operations completed April 10th -
#     Currently supports PNG and JPG images, will support more.

import wx, os, time
from  wx.lib.filebrowsebutton import FileBrowseButton, DirBrowseButton
from functools import partial

from lib.fr0stlib import Flame
from lib.pyflam3 import Genome
from utils import NumberTextCtrl
from config import config
from constants import ID
from _events import EVT_THREAD_MESSAGE, ThreadMessageEvent
from lib.decorators import *



class FreeMemoryPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.GetMem = self.GetMemLinux # TODO: platform specific stuff.
        self.OnUpdate(None)

    def OnUpdate(self, e):
        fgs = wx.FlexGridSizer(2, 2, 1, 1)
        lst = "Free: ", "n/a", "Required: ", self.GetRequiredMem()
        fgs.AddMany(wx.StaticText(self, -1, str(i)) for i in lst)
        self.SetSizer(fgs)
        fgs.Fit(self)

    def GetMemWindows(self):
        pass

    def GetMemLinux(self):
        pass

    def GetRequiredMem(self):
        return "n/a"
        w,h = (self.Parent.dict[i].GetFloat() for i in ("width", "height"))
        if self.Parent.dict["buffer_depth"].GetValue() == '64':
            return w * h * 4. / 1024**2
    
        
        

class RenderDialog(wx.Frame):
    keepratio = True
    depths = {"32-bit int": 32,
              "32-bit float": 33,
              "64-bit int": 64}
    types = {".bmp": wx.BITMAP_TYPE_BMP,
                ".png": wx.BITMAP_TYPE_PNG,
                ".jpg": wx.BITMAP_TYPE_JPEG}

    @BindEvents
    def __init__(self, parent, id):
	self.parent = parent
	style = (wx.DEFAULT_FRAME_STYLE &
                 ~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

	wx.Frame.__init__(self, parent, id, title="Render Flames to Disk",
                          style=style)

        self.config = config["Render-Settings"]
        self.dict = {}
        
        self.gauge = wx.Gauge(self, -1)

        fbb = self.MakeFileBrowseButton()
        flame = self.MakeFlameSelector()
        size = self.MakeSizeSelector()
        opts = self.MakeTCs("quality", "filter", "spatial_oversample",
                            "estimator", "estimator_curve",
                            "estimator_minimum", "highlight_power")
        opts = self.Box("Render Settings", opts)


        mem = self.MakeMemoryWidget()

        self.render = wx.Button(self, ID.RENDER, "Render")

        self.CreateStatusBar()

        for i in "quality", "spatial_oversample", "width", "height":
            tc = self.dict[i]
            tc.MakeIntOnly()
            tc.low = 1
        self.dict["spatial_oversample"].high = 16
        
        szr0 = wx.BoxSizer(wx.VERTICAL)
        szr0.AddMany((size, (mem, 0, wx.EXPAND)))
	szr1 = wx.BoxSizer(wx.HORIZONTAL)
	szr1.AddMany((opts, szr0))
	szr2 = wx.BoxSizer(wx.VERTICAL)
	szr2.AddMany(((fbb, 0, wx.EXPAND), szr1,
                      (self.render, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)))
	szr3 = wx.BoxSizer(wx.HORIZONTAL)
	szr3.AddMany(((flame, 0, wx.EXPAND), (szr2, 0, wx.EXPAND)))
	szr4 = wx.BoxSizer(wx.VERTICAL)
	szr4.AddMany((szr3, (self.gauge, 0, wx.EXPAND)))
	
	self.SetSizer(szr4)
	szr4.Fit(self)

        self.exitflag = 0
        self.rendering = False
	
	self.Center(wx.CENTER_ON_SCREEN)
	self.Show(True)


    def MakeFileBrowseButton(self):
        mask = "PNG File (*.png)|*.png|" \
               "JPG File (*.jpg)|*.jpg|" \
               "BMP File (*.bmp)|*.bmp"
        initial = os.path.join(config["Img-Dir"],
                               self.parent.flame.name+config["Img-Type"])
        fbb = FileBrowseButton(self, -1, fileMask=mask, labelText='File:',
                               initialValue=initial)
        self.fbb = fbb
        return self.Box("Output Destination", (fbb, 0, wx.EXPAND))


    def MakeFlameSelector(self):
	data = self.parent.tree.itemdata
	self.choices = choices = list(self.parent.tree.GetDataList())
	lb = wx.ListBox(self, -1, choices=[f.name for f in choices],
                        style=wx.LB_EXTENDED)
	lb.SetSelection(choices.index(data))
	lb.SetMinSize((180,1))
	self.lb = lb
        btn = wx.Button(self, -1, "All")
        btn.Bind(wx.EVT_BUTTON, lambda e: map(lb.Select, range(len(choices))))
        btn2 = wx.Button(self, -1, "None")
        btn2.Bind(wx.EVT_BUTTON, lambda e: lb.DeselectAll())

	boxhor = wx.BoxSizer(wx.HORIZONTAL)
	boxhor.AddMany((btn, btn2))
	return self.Box("Select Flame(s) to render", boxhor, (lb, 1, wx.EXPAND))


    def MakeSizeSelector(self):
        w,h = 512., 384.
        self.ratio = w/h
        self.config["width"] = w
        self.config["height"] = h
        
        fgs = self.MakeTCs("width", "height", low=0,callback=self.SizeCallback)

        ratio = wx.CheckBox(self, -1, "Keep Ratio")
        ratio.SetValue(True)
        ratio.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)

	return self.Box("Size", fgs, ratio)
    

    def MakeTCs(self, *a, **k):
        fgs = wx.FlexGridSizer(99, 2, 1, 1)
        for i in a:
            tc = NumberTextCtrl(self, **k)
            tc.SetFloat(self.config[i])
            self.dict[i] = tc
            fgs.Add(wx.StaticText(self, -1, i.replace("_", " ").title()),
                    0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            fgs.Add(tc, 0, wx.ALIGN_LEFT, 5)
	return fgs


    def MakeMemoryWidget(self):
        choices = sorted(self.depths.iteritems())
        self.depth = wx.Choice(self, -1, choices=[k for k,_ in choices])
        bits = self.config["buffer_depth"]
        self.depth.SetSelection([v for _,v in choices].index(bits))
        depthtxt = wx.StaticText(self, -1, "Buffer Depth")
        depthszr = wx.BoxSizer(wx.HORIZONTAL)
        depthszr.AddMany(((depthtxt, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5),
                          (self.depth, 0, wx.EXPAND)))
        # TODO: what about setting number of strips?
        return self.Box("Memory Settings", depthszr, FreeMemoryPanel(self))
    

    def Box(self, name, *a):
	box = wx.StaticBoxSizer(wx.StaticBox(self, -1, name),
                                wx.VERTICAL)
	box.AddMany(a)
	return box
    

    def OnCheckBox(self, e):
        self.keepratio = e.GetInt()


    def SizeCallback(self, tc):
        wtc, htc = self.dict["width"], self.dict["height"]
        if self.keepratio:
            v = tc.GetFloat()
            tc.SetInt(v)
            if tc == wtc:
                htc.SetInt(v / self.ratio)
            else:
                wtc.SetInt(v * self.ratio)
        else:
            self.ratio = wtc.GetFloat() / htc.GetFloat()


    @Bind(wx.EVT_CLOSE)
    def OnExit(self, e=None):
        if self.rendering:
            self.SetFocus() # So the user sees where the dialog comes from.
            dlg = wx.MessageDialog(self, 'Abort render?', 'Fr0st',wx.YES_NO)
            res = dlg.ShowModal()
            if res == wx.ID_NO:
                return res
            
        self.CancelRender()
            
        self.parent.renderdialog = None
        self.Destroy()


    @Bind(wx.EVT_BUTTON, id=ID.RENDER)
    def OnRender(self, event):
        if self.render.Label == "Cancel":
            self.CancelRender()
            return

        self.destination = self.fbb.GetValue()
        ty= os.path.splitext(self.destination)[1].lower()
        if ty in self.types:
            config["Img-Type"] = ty
        else:
            wx.MessageDialog(self, "File extension must be png, jpg or bmp.",
                             'Fr0st', wx.OK).ShowModal()
            return
        
        self.selections = self.lb.GetSelections()
        if not self.selections:
            wx.MessageDialog(self, "You must select at least 1 flame.",
                             'Fr0st', wx.OK).ShowModal()
            return

        self.rendering = True
        self.render.Label = "Cancel"    

	kwds = dict((k,v.GetFloat()) for k,v in self.dict.iteritems())
	size = [int(kwds.pop(i)) for i in ("width","height")]
	kwds["buffer_depth"] = self.depths[self.depth.GetStringSelection()]

	config["Render-Settings"].update(kwds)

        req = self.parent.renderer.RenderRequest
        for i in self.selections:
            # TODO: handle repeated names.
            data = self.choices[i]
            req(partial(self.save, data.name, i), data[-1], size,
                progress_func=self.prog, **kwds)

        self.t = time.time()


    def prog(self, *args):
        if self.exitflag:
            self.rendering = False
            return self.exitflag
        wx.PostEvent(self, ThreadMessageEvent(-1, *args))
        

    @Bind(EVT_THREAD_MESSAGE)
    def OnProgress(self, e):
        py_object, fraction, stage, eta = e.GetArgs()
        h = eta/3600
        m = eta%3600/60
        s = eta%60
        self.SetStatusText("rendering: %.2f %%\t\tETA: %02d:%02d:%02d"
                           %(fraction,h,m,s))
        self.gauge.SetValue(fraction)

            
    def CancelRender(self):
        self.exitflag = 1
        # HACK: prevent future renders from being passed to flame.
        del self.parent.renderer.bgqueue[:]
        while self.rendering:
            # waiting for prog func
            time.sleep(0.01)
        self.CleanProg()
        

    def CleanProg(self):
        self.render.Label = "Render"
        self.gauge.SetValue(0)
        self.SetStatusText("")


    def save(self, name, index, bmp):
        if self.exitflag:
            # Don't save image.
            self.exitflag = 0
            return
        ty = config["Img-Type"]
	image = wx.ImageFromBitmap(bmp)
	if len(self.selections) == 1:
            path = self.destination
        else:
            path = os.path.join(os.path.dirname(self.destination), name+ty)
	image.SaveFile(path, self.types[ty])

        if index == self.selections[-1]:
            self.rendering = False
            self.CleanProg()
            
	print time.time() - self.t


