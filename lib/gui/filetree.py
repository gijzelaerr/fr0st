import wx, sys, os, re, shutil, threading
from wx._core import PyDeadObjectError
from threading import Thread

##from ..fr0stlib import Flame
##from ..pyflam3 import Genome
##from .. import functions
##from decorators import *
##from rendering import render

from lib.fr0stlib import Flame
from lib.pyflam3 import Genome
from lib import functions
from decorators import *
from rendering import render

class TreePanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.parent = parent
##        self.log = parent.log
                       
        # Specify a size instead of using wx.DefaultSize
        self.tree = wx.TreeCtrl(self, wx.NewId(), wx.DefaultPosition, (200,500),
                               wx.TR_DEFAULT_STYLE
                               #wx.TR_HAS_BUTTONS
                               | wx.TR_EDIT_LABELS
                               #| wx.TR_MULTIPLE
                               | wx.TR_HIDE_ROOT
                               )

        # Change font size so that it fits nicely with images
        font = self.GetFont()
        font.SetPointSize(11)
        self.tree.SetFont(font)

        # This doesn't work, but the above font resizing does...
##        self.tree.Spacing = 28 # Default is 18
        

        isz = (24,18)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

        self.tree.SetImageList(il)
        self.il = il
        self.isz = isz
        

        self.root = self.tree.AddRoot("The Root Item")
        self.tree.SetPyData(self.root, None)
##        self.tree.SetItemImage(self.root, fldridx, wx.TreeItemIcon_Normal)
##        self.tree.SetItemImage(self.root, fldropenidx, wx.TreeItemIcon_Expanded)

        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit, self.tree)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.tree)
        
        self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)


    @Threaded
    @Catches(PyDeadObjectError)
    def RenderThumbnails(self, item):
##        from time import time
##        t = time()
        il = self.il
##        child,cookie = self.tree.GetFirstChild(item)
##        while child.IsOk():
        for child in self.iterchildren(item):
            string = self.tree.GetPyData(child)
            genome = Genome.from_string(string)[0]
            try:
                il.Add(render(genome,self.isz,quality=20,estimator=3))
                num = il.ImageCount-1
            except:
                num = 2 # Default Icon
            
            self.tree.SetItemImage(child, num)
##            child,cookie = self.tree.GetNextChild(item,cookie)
##        print time() - t


    def iterchildren(self,item):
        child,cookie = self.tree.GetFirstChild(item)
        while child.IsOk():
            yield child
            child,cookie = self.tree.GetNextChild(item,cookie)
            

##    @Bind(wx.EVT_RIGHT_DOWN) # this bind doesn't work
    def OnRightDown(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnRightClick: %s, %s, %s\n" %
                               (self.tree.GetItemText(item), type(item), item.__class__))
            self.tree.SelectItem(item)

##    @Bind(wx.EVT_RIGHT_UP) # this bind doesn't work
    def OnRightUp(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:        
            self.log.WriteText("OnRightUp: %s (manually starting label edit)\n"
                               % self.tree.GetItemText(item))
            self.tree.EditLabel(item)  


    def OnLeftDClick(self, event):
        # This should simply activate a rename...
        event.Skip()


    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self, event):
        self.item = event.GetItem()
        if self.item:
            data = self.tree.GetPyData(self.item)
            if data.startswith("<flame"):
                self.parent.SetFlame(Flame(string=data))
        event.Skip()


    def OnBeginEdit(self, event):
        # This method needs to exist; otherwise On EndEdit is not called
        # correctly. (???)
        event.Skip()
        

    def OnEndEdit(self, event):
        self.item = event.GetItem()
        newname = str(event.GetLabel())
        # Make sure false edits don't accidentally change the name to ""
        if not newname:
            return
        
        if self.tree.GetItemParent(self.item) == self.root:
            path = self.tree.GetPyData(self.item)
            shutil.move(path,os.path.join(os.path.split(path)[0],newname))
            return

        self.parent.flame.name = newname
        newdata = self.parent.flame.to_string()
        self.tree.SetPyData(self.item,newdata)

        # Save the result to the flame file
        parent = self.tree.GetItemParent(self.item)
        lst = [self.tree.GetPyData(i) for i in self.iterchildren(parent)]
        path = self.tree.GetPyData(parent)
        functions.save_flames(path,*lst)

