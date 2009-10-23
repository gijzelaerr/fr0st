#Render Dialog Script for Fr0st
#(Re)Started by Brad on April 6th at 8:00 pm.
#Designed to be a basic dialog that will render the current flame to an image file.
#Changelog:
#   Started April 6th.
#   Basic Operations completed April 10th -
#     Currently supports PNG and JPG images, will support more.

import wx, os, time, sys, itertools
from  wx.lib.filebrowsebutton import FileBrowseButton
from functools import partial
from collections import defaultdict

from fr0stlib import Flame
from fr0stlib.gui.utils import NumberTextCtrl, Box, MyChoice, MakeTCs, SizePanel
from fr0stlib.gui.config import config
from fr0stlib.gui.constants import ID
from fr0stlib.gui._events import InMain
from fr0stlib.decorators import *



class FreeMemoryPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.depth = parent.dict["buffer_depth"]
        self.fgs = wx.FlexGridSizer(2, 2, 1, 1)
        self.SetSizer(self.fgs)


    def UpdateView(self, e=None):
        self.fgs.Clear(True)
        s = "%.2f MB "
        lst = ((" Required Memory: ", 0), (s %self.GetRequired(), wx.ALIGN_RIGHT),
               (" Free Memory: ", 0), (s %self.GetFree(), wx.ALIGN_RIGHT))
        self.fgs.AddMany((wx.StaticText(self, -1, str(i)), 0, fl)
                         for i, fl in lst)
        self.fgs.Layout()
        self.fgs.Fit(self)


    def GetFree(self):
        """Generic Implementation."""
        return wx.GetFreeMemory() / 1024.**2

    def GetMemWindows(self):
        return 0 # TODO: implement this.

    def GetMemLinux(self):
        with open("/proc/meminfo") as f:
            # TODO: not sure if this is entirely correct.
            total, free, buff, cached = (int(f.readline().split()[1])
                                         for i in range(4))
            return (free + cached) / 1024.
        
    try:
        wx.GetFreeMemory()
    except NotImplementedError:   
        if 'win' in sys.platform:
            GetFree = GetMemWindows
        elif 'linux' in sys.platform:
            GetFree = GetMemLinux


    def GetRequired(self):
        w, h = self.Parent.sizepanel.GetInts()
        os = self.Parent.dict["spatial_oversample"].GetFloat()
        int_size = 4
        if self.depth.GetStringSelection() == "64-bit int":
            int_size = 8
        # the *9 is for: 5 in bucket (RGBA+density) + 4 in abucket (RGBA)
        return w * h * os**2 * int_size * 9 / 1024.**2
    
        
        

class RenderDialog(wx.Frame):
    buffer_depth_dict = {"32-bit int": 32,
              "32-bit float": 33,
              "64-bit int": 64}
    types = {".bmp": wx.BITMAP_TYPE_BMP,
             ".png": wx.BITMAP_TYPE_PNG,
             ".jpg": wx.BITMAP_TYPE_JPEG}
    filter_kernel_dict = {"Gaussian": 0,
                          "Hermite": 1,
                          "Box": 2,
                          "Triangle": 3,
                          "Bell": 4,
                          "B_spline": 5,
                          "Lanczos3": 6,
                          "Lanczos2": 7,
                          "Mitchell": 8,
                          "Blackman": 9,
                          "Catrom": 10,
                          "Hamming": 11,
                          "Hanning": 12,
                          "Quadratic": 13}
    nthreads_dict = dict(("%2d" %i, i) for i in range(1, 9))
    nthreads_dict["auto"] = 0

    @BindEvents
    def __init__(self, parent, id):
        self.parent = parent
        style = (wx.DEFAULT_FRAME_STYLE &
                 ~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        wx.Frame.__init__(self, parent, id, title="Render Flames to Disk",
                          style=style)

        self.config = config["Render-Settings"]
        self.dict = {}
        
        self.gauge = wx.Gauge(self, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)

        fbb = self.MakeFileBrowseButton()
        flame = self.MakeFlameSelector()
        mem = self.MakeMemoryWidget()
        self.sizepanel = SizePanel(self, self.mem.UpdateView)
        opts = self.MakeOpts()

        self.render = wx.Button(self, ID.RENDER, "Render")
        self.close = wx.Button(self, ID.CLOSE, "Close")

        self.CreateStatusBar()

        q = self.dict["quality"]
        q.MakeIntOnly()
        q.low = 1
        
        os = self.dict["spatial_oversample"]
        os.MakeIntOnly()
        os.SetAllowedRange(1,16)
        os.callback = self.mem.UpdateView

        # Update size TCs. This needs to be done before setting sizers, to make
        # sure all widgets ahve their final size.
        self.OnSelection()
        
        szr0 = wx.BoxSizer(wx.VERTICAL)
        szr0.AddMany(((mem, 0, wx.EXPAND), self.sizepanel))
        szr1 = wx.BoxSizer(wx.HORIZONTAL)
        szr1.AddMany((opts, szr0))
        szr2 = wx.BoxSizer(wx.VERTICAL)
        btnszr = wx.BoxSizer(wx.HORIZONTAL)
        btnszr.AddMany(((self.render, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM),
                        (self.close, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)))
        szr2.AddMany(((fbb, 0, wx.EXPAND), szr1, (btnszr, 0, wx.ALIGN_RIGHT)))
        szr3 = wx.BoxSizer(wx.HORIZONTAL)
        szr3.AddMany(((flame, 0, wx.EXPAND), (szr2, 0, wx.EXPAND)))
        szr4 = wx.BoxSizer(wx.VERTICAL)
        szr4.AddMany((szr3, (self.gauge, 0, wx.EXPAND)))
	
        self.SetSizer(szr4)
        szr4.Fit(self)

        self.progflag = 0
        self.rendering = False
	
        self.Center(wx.CENTER_ON_SCREEN)
        self.SetBackgroundColour(wx.NullColour)
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
        return Box(self, "Output Destination", (fbb, 0, wx.EXPAND))


    def MakeFlameSelector(self):
        self.lb = lb = wx.ListBox(self, -1, style=wx.LB_EXTENDED)
        self.UpdateFlameSelector()
        lb.SetMinSize((180,1))
        lb.Bind(wx.EVT_LISTBOX, self.OnSelection)
        btn = wx.Button(self, -1, "All")
        btn.Bind(wx.EVT_BUTTON, self.OnSelectAll)
        btn2 = wx.Button(self, -1, "None")
        btn2.Bind(wx.EVT_BUTTON, self.OnDeselectAll)

        boxhor = wx.BoxSizer(wx.HORIZONTAL)
        boxhor.AddMany((btn, btn2))
        return Box(self, "Select Flame(s) to render", boxhor, (lb, 1, wx.EXPAND))


    def UpdateFlameSelector(self):
        for i in range(len(self.lb.GetItems())):
            self.lb.Delete(0)
        data = self.parent.tree.itemdata
        self.choices = choices = list(self.parent.tree.GetDataList())
        self.lb.InsertItems([f.name for f in choices], pos=0)
        self.lb.SetSelection(choices.index(data))


    def MakeOpts(self):
        opts = self.MakeTCs("quality", "spatial_oversample",
                            "estimator", "estimator_curve",
                            "estimator_minimum", "filter_radius")
        filters = self.MakeChoices("filter_kernel", fgs=opts)
        
        early = wx.CheckBox(self, -1, "Early Clip")
        self.earlyclip = self.config["earlyclip"]
        early.SetValue(self.earlyclip)
        early.Bind(wx.EVT_CHECKBOX, self.OnEarly)
        
        transp = wx.CheckBox(self, -1, "PNG Transparency")
        self.transp = self.config["transparent"]
        transp.SetValue(self.transp)
        transp.Bind(wx.EVT_CHECKBOX, self.OnTransp)
        
        return Box(self, "Render Settings", opts, early, transp)

    
    def MakeMemoryWidget(self):
        # TODO: what about setting number of strips?
        depthszr = self.MakeChoices("buffer_depth", "nthreads")
        self.mem = FreeMemoryPanel(self)
        self.dict["buffer_depth"].Bind(wx.EVT_CHOICE, self.mem.UpdateView)
        return Box(self, "Resource Usage", depthszr, self.mem)


    def MakeTCs(self, *a, **k):
        """Wrapper around MakeTCs that adds all tcs to self.dict."""
        fgs, d = MakeTCs(self, *((i, self.config[i]) for i in a), **k)
        self.dict.update(d)
        return fgs


    def MakeChoices(self, *a, **k):
        fgs = k["fgs"] if "fgs" in k else wx.FlexGridSizer(99, 2, 1, 1)
        for i in a:
            widg = MyChoice(self, i, getattr(self, i+"_dict"), self.config[i])
            self.dict[i] = widg
            fgs.Add(wx.StaticText(self, -1, i.replace("_", " ").title()),
                    0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            fgs.Add(widg, 0, wx.ALIGN_RIGHT, 5)
        return fgs


    def OnEarly(self, e):
        self.earlyclip = e.GetInt()


    def OnTransp(self, e):
        self.transp = e.GetInt()


    @Catches(wx.PyDeadObjectError)
    def OnSelection(self, e=None):
        selections = self.lb.GetSelections()
        len_ = len(selections)
        if not len_:
            return
        elif len_ == 1:
            name = self.choices[selections[0]]._name
        else:
            name = "{name}"
        path = self.fbb.GetValue()
        ext = os.path.splitext(path)[1]
        self.fbb.SetValue(os.path.join(os.path.dirname(path), name) + ext)

        tempflame = Flame(self.choices[selections[0]][-1])
        self.sizepanel.UpdateSize(tempflame.size)
        self.mem.UpdateView()

        
    def OnSelectAll(self, e=None):
        map(self.lb.Select, range(len(self.choices)))
        self.OnSelection()


    def OnDeselectAll(self, e=None):
        self.lb.DeselectAll()
##        self.OnSelection()


    def UpdateView(self):
        if self.rendering:
            return
        self.UpdateFlameSelector()
        self.OnSelection()
        

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


    @Bind(wx.EVT_BUTTON, id=ID.CLOSE)
    def OnClose(self, e):
        if self.close.Label == "Cancel":
            self.CancelRender()
        else:
            self.OnExit()
        

    @Bind(wx.EVT_BUTTON, id=ID.RENDER)
    def OnRender(self, event):
        if self.render.Label == "Pause":
            self.render.Label = "Resume"
            self.progflag = 2
            return
        elif self.render.Label == "Resume":
            self.render.Label = "Pause"
            self.progflag = 0
            return

        destination = self.fbb.GetValue()
        ty= os.path.splitext(destination)[1].lower()
        if ty not in self.types:
            wx.MessageDialog(self, "File extension must be png, jpg or bmp.",
                             'Fr0st', wx.OK).ShowModal()
            return
        
        self.selections = self.lb.GetSelections()
        if not self.selections:
            wx.MessageDialog(self, "You must select at least 1 flame.",
                             'Fr0st', wx.OK).ShowModal()
            return

        if self.mem.GetRequired() > self.mem.GetFree() + .5:
            # TODO: offer between slicing and cancel
            wx.MessageDialog(self, "Not enough memory for render.",
                             'Fr0st', wx.OK).ShowModal()
            return

        # Interpolate flame names, make repeated names unique, and ensure all
        # paths are legal by calling the os.
        paths = []
        d = defaultdict(lambda: itertools.count(2).next)
        for i in self.selections:
            data = self.choices[i]
            try:
                path = destination.format(name=data._name)
                if path in paths:
                    base, ext = os.path.splitext(path)
                    path = "%s (%s)%s" %(base, d[path](), ext)
                # Check if path is valid and user has write permission.
                if os.path.exists(path):
                    open(path, 'a').close()
                else:
                    dirname = os.path.dirname(path)
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
                    open(path, 'w').close()
                    os.remove(path)
            except (KeyError, ValueError, IndexError, IOError):
                wx.MessageDialog(self, "Invalid path name.", 'Fr0st',
                                 wx.OK).ShowModal()
                return
            paths.append(path)

        clashes = [path for path in paths if os.path.exists(path)]
        if clashes:
            if len(clashes) > 3:
                middle = "%%s\n... (%s more)\n\n" %len(clashes[3:])
                clashes = clashes[:3]
            else:
                middle = "%s\n\n"
            string = ("The following file%s already exist%s:\n" + 
                      middle + 
                      "Do you want to overwrite?")
            s1, s2 = ("s", "") if len(clashes) > 1 else ("", "s")
            if wx.MessageDialog(self, string %(s1, s2, "\n".join(clashes)),
                                'Fr0st', wx.YES_NO).ShowModal() == wx.ID_NO:
                return

        # All checks have been made, the render is confirmed.
        self.rendering = True
        self.close.Label = "Cancel"
        self.render.Label = "Pause"

        kwds = dict((k,v.GetFloat()) for k,v in self.dict.iteritems())
        kwds["earlyclip"] = self.earlyclip
        if ty == ".png":
            kwds["transparent"] = self.transp
        size = self.sizepanel.GetInts()

        self.config.update(kwds)
        config["Img-Dir"] = os.path.dirname(destination)
        config["Img-Type"] = ty

        req = self.parent.renderer.RenderRequest
        backup = open(os.path.join(wx.GetApp().ConfigDir,'renders.flame'), 'a')
        for i, path in zip(self.selections, paths):
            data = self.choices[i]
            prog = self.MakeProg(data.name, self.selections.index(i)+1,
                                 len(self.selections))
            req(partial(self.save, path, i), data[-1], size,
                progress_func=prog, **kwds)
            backup.write(data[-1] + "\n")
        backup.close()

        self.t = time.time()


    def MakeProg(self, name, index, lenght):
        string = "rendering %s/%s (%s): %%.2f %%%% \t" %(index, lenght, name)
        str_iter = string + "ETA: %02d:%02d:%02d"
        str_de = string + "running density estimation"
        def prog(*args):
            if self.progflag == 1:
                self.rendering = False
                return 1
            self.OnProgress(str_iter, str_de, *args)
            return self.progflag
        return prog
        

    @InMain
    def OnProgress(self, str_iter, str_de, py_object, fraction, stage, eta):
        if stage == 0:
            h = eta/3600
            m = eta%3600/60
            s = eta%60
            self.SetStatusText(str_iter % (fraction,h,m,s))
            self.gauge.SetValue(fraction)
        else:
            self.SetStatusText(str_de % fraction)

            
    def CancelRender(self):
        self.progflag = 1
        # HACK: prevent future renders from being passed to flame.
        del self.parent.renderer.bgqueue[:]
        while self.rendering:
            # waiting for prog func
            time.sleep(0.01)
        

    def CleanProg(self):
        self.render.Label = "Render"
        self.close.Label = "Close"
        self.gauge.SetValue(0)
        self.SetStatusText("")


    def save(self, path, index, bmp):
        if self.progflag:
            # Don't save image.
            self.progflag = 0
            self.CleanProg()
            return
        ty = config["Img-Type"]
        wx.ImageFromBitmap(bmp).SaveFile(path, self.types[ty])

        if index == self.selections[-1]:
            self.rendering = False
            self.CleanProg()
