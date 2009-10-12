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

from lib.fr0stlib import Flame
from lib.gui.utils import NumberTextCtrl, Box, MyChoice
from lib.gui.config import config
from lib.gui.constants import ID
from lib.gui._events import InMain
from lib.decorators import *



class FreeMemoryPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.depth = parent.dict["buffer_depth"]
        self.fgs = wx.FlexGridSizer(2, 2, 1, 1)
        self.SetSizer(self.fgs)
        self.UpdateView()


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
        w, h = (self.Parent.dict[i].GetFloat() for i in ("width", "height"))
        os = self.Parent.dict["spatial_oversample"].GetFloat()
        int_size = 4
        if self.depth.GetStringSelection() == "64-bit int":
            int_size = 8
        # the *9 is for: 5 in bucket (RGBA+density) + 4 in abucket (RGBA)
        return w * h * os**2 * int_size * 9 / 1024.**2
    
        
        

class RenderDialog(wx.Frame):
    keepratio = True
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
    nthreads_dict = dict(("%2d" %i, i) for i in range(1, 17))
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
        
        self.gauge = wx.Gauge(self, -1)

        fbb = self.MakeFileBrowseButton()
        flame = self.MakeFlameSelector()
        size = self.MakeSizeSelector()
        opts = self.MakeOpts()
        mem = self.MakeMemoryWidget()

        self.render = wx.Button(self, ID.RENDER, "Render")

        self.CreateStatusBar()

        for i in "quality", "width", "height":
            tc = self.dict[i]
            tc.MakeIntOnly()
            tc.low = 1
        os = self.dict["spatial_oversample"]
        os.MakeIntOnly()
        os.SetAllowedRange(1,16)
        os.callback = self.mem.UpdateView
        
        szr0 = wx.BoxSizer(wx.VERTICAL)
        szr0.AddMany(((mem, 0, wx.EXPAND), size))
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
        if "win" in sys.platform:
            # TODO: need a cleaner way to make this look right in windows.
            self.SetBackgroundColour((255,255,255))
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


    def MakeSizeSelector(self):
        # HACK: those are arbitrary values, just so MakeTCs doesn't choke.
        self.config["width"] = 512.
        self.config["height"] = 384.    
        fgs = self.MakeTCs("width", "height", low=0,callback=self.SizeCallback)

        # Update tc to show flame size.
        self.OnSelection()

        ratio = wx.CheckBox(self, -1, "Keep Ratio")
        ratio.SetValue(True)
        ratio.Bind(wx.EVT_CHECKBOX, self.OnRatio)

        return Box(self, "Size", fgs, ratio)


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
        fgs = wx.FlexGridSizer(99, 2, 1, 1)
        for i in a:
            tc = NumberTextCtrl(self, **k)
            tc.SetFloat(self.config[i])
            self.dict[i] = tc
            fgs.Add(wx.StaticText(self, -1, i.replace("_", " ").title()),
                    0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            fgs.Add(tc, 0, wx.ALIGN_RIGHT, 5)
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


    def OnRatio(self, e):
        self.keepratio = e.GetInt()


    def OnEarly(self, e):
        self.earlyclip = e.GetInt()


    def OnTransp(self, e):
        self.transp = e.GetInt()


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
            self.ratio = float(wtc.GetInt()) / htc.GetInt()
        self.mem.UpdateView()


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
        self.dict["width"].SetFloat(tempflame.width)
        self.dict["height"].SetFloat(tempflame.height)
        self.ratio = float(tempflame.width) / tempflame.height

        
    def OnSelectAll(self, e=None):
        map(self.lb.Select, range(len(self.choices)))
        self.OnSelection()


    def OnDeselectAll(self, e=None):
        self.lb.DeselectAll()
##        self.OnSelection()


    def UpdateView(self):
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


    @Bind(wx.EVT_BUTTON, id=ID.RENDER)
    def OnRender(self, event):
        if self.render.Label == "Cancel":
            self.CancelRender()
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
        self.render.Label = "Cancel"

        kwds = dict((k,v.GetFloat()) for k,v in self.dict.iteritems())
        kwds["earlyclip"] = self.earlyclip
        if ty == ".png":
            kwds["transparent"] = self.transp
        size = [int(kwds.pop(i)) for i in ("width","height")]

        self.config.update(kwds)
        config["Img-Dir"] = os.path.dirname(destination)
        config["Img-Type"] = ty

        req = self.parent.renderer.RenderRequest
        backup = open('renders.flame', 'a')
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
            if self.exitflag:
                self.rendering = False
                return self.exitflag
            self.OnProgress(str_iter, str_de, *args)
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
        self.exitflag = 1
        # HACK: prevent future renders from being passed to flame.
        del self.parent.renderer.bgqueue[:]
        while self.rendering:
            # waiting for prog func
            time.sleep(0.01)
        

    def CleanProg(self):
        self.render.Label = "Render"
        self.gauge.SetValue(0)
        self.SetStatusText("")


    def save(self, path, index, bmp):
        if self.exitflag:
            # Don't save image.
            self.exitflag = 0
            self.CleanProg()
            return
        ty = config["Img-Type"]
        wx.ImageFromBitmap(bmp).SaveFile(path, self.types[ty])

        if index == self.selections[-1]:
            self.rendering = False
            self.CleanProg()

        # TODO: remove
        print time.time() - self.t


