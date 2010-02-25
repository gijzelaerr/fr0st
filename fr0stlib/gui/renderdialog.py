##############################################################################
#  Fractal Fr0st - fr0st
#  https://launchpad.net/fr0st
#
#  Copyright (C) 2009 by Vitor Bosshard <algorias@gmail.com>
#
#  Fractal Fr0st is free software; you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this library; see the file COPYING.LIB.  If not, write to
#  the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 02111-1307, USA.
##############################################################################

import wx, os, time, sys, itertools
from  wx.lib.filebrowsebutton import FileBrowseButton
from collections import defaultdict

from fr0stlib import Flame
from fr0stlib.gui.utils import NumberTextCtrl, Box, MyChoice, MakeTCs, SizePanel
from fr0stlib.gui.config import config
from fr0stlib.gui.constants import ID
from fr0stlib.gui._events import InMain
from fr0stlib.decorators import *
from fr0stlib.render import save_image



class FreeMemoryPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.depth = parent.GetParent().dict["buffer_depth"]
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
        w, h = self.GetParent().GetParent().sizepanel.GetInts()
        os = self.GetParent().GetParent().dict["spatial_oversample"].GetFloat()
        depth = int(self.depth.GetStringSelection().split("-")[0]) / 8
        # the *9 is for: 5 in bucket (RGBA+density) + 4 in abucket (RGBA)
        return w * h * os**2 * depth * 9 / 1024.**2
    
        
        

class RenderDialog(wx.Frame):
    buffer_depth_dict = {"32-bit int": 32,
              "32-bit float": 33,
              "64-bit double": 64}
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

        wx.GetApp().LoadIconsInto(self)

        self.config = config["Render-Settings"]
        self.dict = {}
        self.progflag = 0
        self.rendering = False
        
        #NOTE: On windows, all child controls must not have a frame as their direct
        #NOTE: parent if you want to use tab traversal. There MUST be a panel between
        #NOTE: the control an the frame in the window heirarchy.
        main_panel = wx.Panel(self)
        
        self.gauge = wx.Gauge(main_panel, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)

        fbb = self.MakeFileBrowseButton(main_panel)
        flame = self.MakeFlameSelector(main_panel)
        mem = self.MakeMemoryWidget(main_panel)
        self.sizepanel = SizePanel(main_panel, self.mem.UpdateView)
        opts = self.MakeOpts(main_panel)

        self.render = wx.Button(main_panel, ID.RENDER, "Render")
        self.close = wx.Button(main_panel, ID.CLOSE, "Close")

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
	
        main_panel.SetSizer(szr4)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(main_panel, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        #szr4.Fit(self)
	
        self.Center(wx.CENTER_ON_SCREEN)
        self.SetBackgroundColour(wx.NullColour)
        self.SetDoubleBuffered(True)
        self.Show(True)

        prev = self.flame_select_all
        tab_order = [
                    self.flame_select_none,
                    self.lb,
                    self.fbb,
                    self.dict['quality'], 
                    self.dict['spatial_oversample'],
                    self.dict['estimator'],
                    self.dict['estimator_curve'],
                    self.dict['estimator_minimum'],
                    self.dict['filter_radius'],
                    self.dict['filter_kernel'],
                    self.check_early_clip,
                    self.check_transparent,
                    self.dict['buffer_depth'],
                    self.dict['nthreads'],
                ]

        for x in tab_order:
            x.MoveAfterInTabOrder(prev)
            prev = x


    def MakeFileBrowseButton(self, parent):
        mask = "PNG File (*.png)|*.png|" \
               "JPG File (*.jpg)|*.jpg|" \
               "BMP File (*.bmp)|*.bmp"
        initial = os.path.join(config["Img-Dir"], 
                               self.parent.flame.name + config["Img-Type"])
        fbb = FileBrowseButton(parent, -1, fileMask=mask, labelText='File:',
                               initialValue=initial, fileMode=wx.SAVE)
        self.fbb = fbb
        return Box(parent, "Output Destination", (fbb, 0, wx.EXPAND))


    def MakeFlameSelector(self, parent):
        self.flame_select_all = btn = wx.Button(parent, -1, "All")
        btn.Bind(wx.EVT_BUTTON, self.OnSelectAll)

        self.flame_select_none = btn2 = wx.Button(parent, -1, "None")
        btn2.Bind(wx.EVT_BUTTON, self.OnDeselectAll)

        self.lb = lb = wx.ListBox(parent, -1, style=wx.LB_EXTENDED)
        self.UpdateFlameSelector()
        lb.SetMinSize((180,1))
        lb.Bind(wx.EVT_LISTBOX, self.OnSelection)

        boxhor = wx.BoxSizer(wx.HORIZONTAL)
        boxhor.AddMany((btn, btn2))
        return Box(parent, "Select Flame(s) to render", boxhor, (lb, 1, wx.EXPAND))


    def UpdateFlameSelector(self):
        for i in range(len(self.lb.GetItems())):
            self.lb.Delete(0)
        data = self.parent.tree.itemdata
        self.choices = choices = list(self.parent.tree.GetDataGen())
        self.lb.InsertItems([f.name for f in choices], pos=0)
        self.lb.SetSelection(choices.index(data))


    def MakeOpts(self, parent):
        opts = self.MakeTCs(parent, 
                            "quality", "spatial_oversample",
                            "estimator", "estimator_curve",
                            "estimator_minimum", "filter_radius")
        filters = self.MakeChoices(parent, "filter_kernel", fgs=opts)
        
        early = wx.CheckBox(parent, -1, "Early Clip")
        self.earlyclip = self.config["earlyclip"]
        self.check_early_clip = early
        early.SetValue(self.earlyclip)
        early.Bind(wx.EVT_CHECKBOX, self.OnEarly)
        
        transp = wx.CheckBox(parent, -1, "PNG Transparency")
        self.transp = self.config["transparent"]
        self.check_transparent = transp
        transp.SetValue(self.transp)
        transp.Bind(wx.EVT_CHECKBOX, self.OnTransp)
        
        return Box(parent, "Render Settings", opts, early, transp)

    
    def MakeMemoryWidget(self, parent):
        # TODO: what about setting number of strips?
        depthszr = self.MakeChoices(parent, "buffer_depth", "nthreads")
        self.mem = FreeMemoryPanel(parent)
        self.dict["buffer_depth"].Bind(wx.EVT_CHOICE, self.mem.UpdateView)
        return Box(parent, "Resource Usage", depthszr, self.mem)


    def MakeTCs(self, parent, *a, **k):
        """Wrapper around MakeTCs that adds all tcs to self.dict."""
        fgs, d = MakeTCs(parent, *((i, self.config[i]) for i in a), **k)
        self.dict.update(d)
        return fgs


    def MakeChoices(self, parent, *a, **k):
        fgs = k["fgs"] if "fgs" in k else wx.FlexGridSizer(99, 2, 1, 1)
        for i in a:
            widg = MyChoice(parent, i, getattr(self, i+"_dict"), self.config[i])
            self.dict[i] = widg
            fgs.Add(wx.StaticText(parent, -1, i.replace("_", " ").title()),
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
            
        self.progflag = 1            
        self.parent.renderdialog = None
        self.Destroy()


    @Bind(wx.EVT_BUTTON, id=ID.CLOSE)
    def OnClose(self, e):
        self.progflag = 1
        if self.close.Label == "Close":
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
        if ty not in (".bmp", ".png", ".jpg"):
            wx.MessageDialog(self, "File extension must be png, jpg or bmp.",
                             'Fr0st', wx.OK).ShowModal()
            return
        
        selections = [self.choices[i] for i in self.lb.GetSelections()]
        if not selections:
            wx.MessageDialog(self, "You must select at least 1 flame.",
                             'Fr0st', wx.OK).ShowModal()
            return

        if self.mem.GetRequired() > self.mem.GetFree() + .5:
            # TODO: offer between slicing and cancel
            wx.MessageDialog(self, "Not enough memory for render.",
                             'Fr0st', wx.OK).ShowModal()
            return

        # Interpolate flame names, make repeated names unique.
        paths = [destination.format(name=data._name) for data in selections]
        check = defaultdict(int)
        for path in paths:
            check[path] += 1
        if len(check) < len(paths):
            d = defaultdict(lambda: itertools.count(1).next)
            def uniq(path):
                if check[path] > 1:
                    base, ext = os.path.splitext(path)
                    return "%s (%04d)%s" %(base, d[path](), ext)
                return path
            paths = map(uniq, paths)

        # Check if each path is valid and user has write permission.
        for path in paths:
            try:
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

        clashes = filter(os.path.exists, paths)
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
        self.render.Label = "Pause"
        self.close.Label = "Cancel"

        kwds = dict((k,v.GetFloat()) for k,v in self.dict.iteritems())
        kwds["earlyclip"] = self.earlyclip
        if ty == ".png":
            kwds["transparent"] = self.transp

        self.config.update(kwds)
        config["Img-Dir"] = os.path.dirname(destination)
        config["Img-Type"] = ty

        self._gen = self.render_gen(selections, paths, kwds)
        self._gen.next()


    def render_gen(self, selections, paths, kwds):
        size = self.sizepanel.GetInts()
        len_ = len(selections)
        old_title = self.Title
        req = self.parent.renderer.RenderRequest
        backup = open(os.path.join(wx.GetApp().ConfigDir,'renders.bak'), 'a')

        for i, (data, path) in enumerate(zip(selections, paths)):
            name = data.name if len(data.name) < 20 else data.name[:17] + "..."
            str_name = "Rendering %s/%s (%s)" %(i+1, len_, name)
            req(self._gen.send, data[-1], size,
                progress_func=self.MakeProg(str_name), **kwds)
            backup.write(data[-1] + "\n")
            self.Title = str_name
            bmp = yield
            if self.progflag:
                self.progflag = 0
                break
            save_image(path, bmp)
            
        backup.close()
        self.Title = old_title
        self.gauge.SetValue(0)
        self.SetStatusText("")
        
        self.rendering = False
        self.render.Label = "Render"
        self.close.Label = "Close"
        yield
        

    def MakeProg(self, str_name):
        str_it = str_name + ": %.2f %% \tETA: %02d:%02d:%02d"
        str_de = str_name + ": %.2f %% \tRunning density estimation"
        
        @InMain
        @Catches(wx.PyDeadObjectError)
        def prog(py_object, fraction, stage, eta):
            if stage == 0:
                h, m, s = eta/3600, eta%3600/60, eta%60
                self.SetStatusText(str_it % (fraction, h, m, s))
                self.gauge.SetValue(fraction)
            else:
                self.SetStatusText(str_de % fraction)
            return self.progflag
        return prog

