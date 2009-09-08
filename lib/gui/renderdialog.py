#Render Dialog Script for Fr0st
#(Re)Started by Brad on April 6th at 8:00 pm.
#Designed to be a basic dialog that will render the current flame to an image file.
#Changelog:
#   Started April 6th.
#   Basic Operations completed April 10th -
#     Currently supports PNG and JPG images, will support more.

import wx, os, time
from  wx.lib.filebrowsebutton import FileBrowseButton

from lib.fr0stlib import Flame
from lib.pyflam3 import Genome
from utils import NumberTextCtrl
from _events import EVT_THREAD_MESSAGE, ThreadMessageEvent
from lib.decorators import *

class RenderDialog(wx.Frame):

    @BindEvents
    def __init__(self, parent, id):
	self.parent = parent
	
	wx.Frame.__init__(self, parent, id,
                           title="Render Flame to Image File",
                           size=(400,210))#TODO:Change title to say name 
					  #of current flame - self.parent.flame.name
             
        #Destination Box
        wx.StaticBox(self, 1,"Destination:", pos=(5, 5),size=(390,55)) 
        wx.StaticText(self, 1, "Output Destination:",pos=(10,20))
        self.txtDestination = wx.TextCtrl(self, 1, '',pos=(10,35),size=(280,22))
        wx.Button(self, 3, ". . .", pos=(300,35),size=(75,22))

        #Size Box
        wx.StaticBox(self, 2, "Size:", pos=(5,60),size=(180,75))
        wx.StaticText(self, 2, "Width:", pos=(10,75))
        wx.StaticText(self, 2, "Height:", pos=(10,110))
        self.Width = wx.ComboBox(self, 2, '', pos=(50,70), size=(130,22),
                                 choices=('320','640','1024','1280','2048'))
        self.Height = wx.ComboBox(self, 2, '', pos=(50,105), size=(130,22),
                                  choices=('240','480','768','1024','1536'))
        #Initialize the Values
        self.Width.SetValue("1024")
        self.Height.SetValue("768")
        
        #Quality Box
        wx.StaticBox(self, 3, "Render Options:", pos=(200,60),size=(195,75))
        wx.StaticText(self, 3, "Quality:", pos=(207,80))
        wx.StaticText(self, 3, "Estimator:", pos=(207,110))
        self.Quality = wx.SpinCtrl(self, 3, '', pos=(250,75),size=(140,22))
        self.Quality.SetRange(1,150000)
        self.Estimator = wx.TextCtrl(self, 3, '', pos=(260,105), size=(130,22))
        self.Estimator.SetValue('9')
        #TODO - Add more options. Oversample, etc.
        
        wx.Button(self, 1, "Begin Render", pos=(10,150))
        wx.Button(self, 2, "Close", pos=(300,150))

        self.exitflag = 0
        self.rendering = False
        
        self.Centre()
        self.Show(1)


    @Bind(wx.EVT_BUTTON, id=3)
    def chooseOutputFile(self, event):
        filters = 'All files (*.*)|*.*|PNG File (*.png)|*.png|JPG File (*.jpg)|*.jpg'
        dlg=wx.FileDialog(self, "Choose the Output File", os.getcwd(),
                          "", filters, wx.SAVE)
        if dlg.ShowModal()==wx.ID_OK:
            path = dlg.GetPath()
            self.txtDestination.SetValue(path)         
        dlg.Destroy()


    @Bind(wx.EVT_CLOSE)
    @Bind(wx.EVT_BUTTON, id=2)
    def closeDialog(self, e=None):
        # TODO: dialog confirming exit (and cancelling render if yes)
        if self.rendering:
            self.SetFocus() # So the user sees where the dialog comes from.
            dlg = wx.MessageDialog(self, 'Abort render?' ,
                                   'Fr0st',wx.YES_NO)
            res = dlg.ShowModal()
            if res == wx.ID_NO:
                return res
            
        self.exitflag = 1
        while self.rendering:
            # waiting for prog func
            time.sleep(0.1)
            
        self.parent.renderdialog = None
        self.Destroy()


    @Bind(wx.EVT_BUTTON, id=1)
    def beginRender(self, event):
        destination = str(self.txtDestination.GetValue())
	#GetValue() returns unicode, change to string
	type = os.path.splitext(destination)[1]
        size = int(self.Width.GetValue()),int(self.Height.GetValue())
	#GetValue() returns unicode, change to int
	
	self.utype = type.upper()
	if self.utype == '.PNG': self.wxFormat = wx.BITMAP_TYPE_PNG
        elif self.utype == '.JPG': self.wxFormat = wx.BITMAP_TYPE_JPG
	elif self.utype == '.BMP': self.wxFormat = wx.BITMAP_TYPE_BMP
	elif self.utype == '.GIF': self.wxFormat = wx.BITMAP_TYPE_GIF
	elif self.utype == '.PNM': self.wxFormat = wx.BITMAP_TYPE_PNM
	elif self.utype == '.XPM': self.wxFormat = wx.BITMAP_TYPE_XPM
	elif self.utype == '.TIF': self.wxFormat = wx.BITMAP_TYPE_TIF
	else: raise ValueError(self.utype)

	flame = self.parent.flame

        # TODO: filter shouldn't be hardcoded.
	req = self.parent.renderer.RenderRequest
	req(self.save, flame, size, self.Quality.GetValue(),
            int(self.Estimator.GetValue()), filter=.2, progress_func=self.prog)

        self.rendering = True
        self.t = time.time()


    def prog(self, py_object, fraction, stage, eta):
        print 'rendering: %.2f%% ETA: %.0f seconds' % (fraction,eta)
        if self.exitflag:
            self.rendering = False
            return self.exitflag


    def save(self, bmp):
	image = wx.ImageFromBitmap(bmp)
	destination = str(self.txtDestination.GetValue())
	image.SaveFile(destination, self.wxFormat)

	self.rendering = False
	print time.time() - self.t



class FreeMemoryPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.OnUpdate(None)

    def OnUpdate(self, e):
        fgs = wx.FlexGridSizer(2, 2, 1, 1)
        lst = "Free: ", "n/a", "Required: ", "n/a"
        fgs.AddMany(wx.StaticText(self, -1, i) for i in lst)
        self.SetSizer(fgs)
        fgs.Fit(self)
        
        

class RenderDialogUnderConstruction(wx.Frame):
    keepratio = True

    @BindEvents
    def __init__(self, parent, id):
	self.parent = parent
	self.dict = {}
	
	wx.Frame.__init__(self, parent, id,
                           title="Render Flames to Disk",)
##                           size=(400,210))

        fbb = FileBrowseButton(self, -1, changeCallback=self.fbbCallback)

        self.gauge = wx.Gauge(self, -1)

        flame = self.MakeFlameSelector()
        size = self.MakeSizeSelector()
        opts = self.MakeTCs("quality", "filter", "spatial_oversample",
                            "estimator", "estimator_curve",
                            "estimator_minimum", "highlight_power")
        opts = self.Box("Settings", opts)


        mem = self.Box("Memory", FreeMemoryPanel(self))
        
        szr0 = wx.BoxSizer(wx.VERTICAL)
        szr0.AddMany((size, (mem, 0, wx.EXPAND)))
	szr1 = wx.BoxSizer(wx.HORIZONTAL)
	szr1.AddMany((opts, szr0))
	szr2 = wx.BoxSizer(wx.VERTICAL)
	szr2.AddMany(((fbb, 0, wx.EXPAND), szr1))
	szr3 = wx.BoxSizer(wx.HORIZONTAL)
	szr3.AddMany((flame, szr2))
	szr4 = wx.BoxSizer(wx.VERTICAL)
	szr4.AddMany((szr3, (self.gauge, 0, wx.EXPAND)))
	
	self.SetSizer(szr4)
	szr4.Fit(self)
	self.Show(True)


    def MakeFlameSelector(self):
	data = self.parent.tree.itemdata
	choices = list(self.parent.tree._GetFlames())
	lb = wx.ListBox(self, -1, size=(180,300),
                         choices=[f.name for f in choices],
                         style=wx.LB_EXTENDED)
	lb.SetSelection(choices.index(data))
        btn = wx.Button(self, -1, "All")
        btn.Bind(wx.EVT_BUTTON, lambda e: map(lb.Select, range(len(choices))))
        btn2 = wx.Button(self, -1, "None")
        btn2.Bind(wx.EVT_BUTTON, lambda e: lb.DeselectAll())

	boxhor = wx.BoxSizer(wx.HORIZONTAL)
	boxhor.AddMany((btn, btn2))
	return self.Box("Select Flame(s) to render", boxhor, lb)


    def MakeSizeSelector(self):
        fgs = self.MakeTCs("width", "height",
                           low=0, callback=self.SizeCallback)
        w,h = 1024., 768.
        self.ratio = w/h
        self.dict["width"].SetInt(w)
        self.dict["height"].SetInt(h)
        
        ratio = wx.CheckBox(self, -1, "Keep Ratio")
        ratio.SetValue(True)
        ratio.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)

	return self.Box("Size", fgs, ratio)


    def MakeTCs(self, *a, **k):
        fgs = wx.FlexGridSizer(99, 2, 1, 1)
        for i in a:
            tc = NumberTextCtrl(self, **k)
            self.dict[i] = tc
            fgs.Add(wx.StaticText(self, -1, i.replace("_", " ").title()),
                    0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            fgs.Add(tc, 0, wx.ALIGN_LEFT, 5)

	return fgs
      

    def Box(self, name, *a):
	box = wx.StaticBoxSizer(wx.StaticBox(self, -1, name),
                                wx.VERTICAL)
	box.AddMany(a)
	return box
    

    def OnCheckBox(self, e):
        self.keepratio = e.GetInt()


    def SizeCallback(self, tc):
        if self.keepratio:
            v = tc.GetFloat()
            tc.SetInt(v)
            if tc == self.wtc:
                self.htc.SetInt(v / self.ratio)
            else:
                self.wtc.SetInt(v * self.ratio)
        else:
            self.ratio = self.wtc.GetFloat() / self.htc.GetFloat()


    def fbbCallback(self, e):
        self.path = e.GetString()
         
        
