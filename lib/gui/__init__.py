from __future__ import with_statement
import os, sys, wx, time, re, functools, threading
from wx import PyDeadObjectError

from lib.gui.editor import EditorFrame 
from lib.gui.filetree import TreePanel
from lib.gui.menu import CreateMenu
from lib.gui.toolbar import CreateToolBar
from lib.gui.decorators import *
from lib.gui.constants import ID
from lib.gui.canvas import XformCanvas
from lib.threadinterrupt import interruptall
from lib._exceptions import ThreadInterrupt
from lib import functions
from lib.pyflam3 import Genome
from lib.gui.rendering import render, Renderer
from lib.gui._events import EVT_IMAGE_READY, CanvasRefreshEvent
from lib.fr0stlib import Flame


class MainWindow(wx.Frame):
    re_name = re.compile(r'(?<= name=").*?(?=")')
    flame = None

    @BindEvents    
    def __init__(self,parent,id):
        self.title = "Fractal Fr0st"
        wx.Frame.__init__(self,parent,wx.ID_ANY, self.title)    

        # This icon stuff is not working...
##        ib=wx.IconBundle()
##        ib.AddIconFromFile("Icon.ico",wx.BITMAP_TYPE_ANY)
##        self.SetIcons(ib)
        self.CreateStatusBar()
        self.SetMinSize((800,600))
        self.SetDoubleBuffered(True)
        
        # Launch the render thread
        self.renderer = Renderer(self)
        
        # Creating Frame Content
        CreateMenu(self)
        CreateToolBar(self)
        self.image = ImagePanel(self)
        self.canvas = XformCanvas(self)

        self.editorframe = EditorFrame(self, wx.ID_ANY)
        self.editor = self.editorframe.editor
        self.log = self.editorframe.log 
        
        self.TreePanel = TreePanel(self)
        self.tree = self.TreePanel.tree
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.TreePanel,0,wx.EXPAND)
        sizer.Add(self.canvas,0)
        sizer.Add(self.image,0,wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        sizer.Fit(self)

        self.wildcard = "Flame file (*.flame)|*.flame|" \
                        "All files (*.*)|*.*"

        # Set up paths
        sys.path.append(os.path.join(sys.path[0],"scripts")) # imp in scripts
        self.flamepath = os.path.join(sys.path[0],"parameters","samples.flame")
        self.OpenFlameFile(self.flamepath)

        self.Show(1)
    

#-----------------------------------------------------------------------------
# Event handlers

    @Bind(wx.EVT_MENU,id=ID.ABOUT)
    def OnAbout(self,e):
        d= wx.MessageDialog(self,
                            " TODO", wx.OK)
        d.ShowModal()
        d.Destroy()


    @Bind(wx.EVT_CLOSE)
    @Bind(wx.EVT_MENU,id=ID.EXIT)
    def OnExit(self,e):

        self.OnStopScript()
        
        # check for differences in flame file
        if self.flame:
            oldflame = Flame(string=self.tree.GetPyData(self.TreePanel.item))
            if self.flame.to_string() != oldflame.to_string():
                dlg = wx.MessageDialog(self, 'Save changes?',
                                       'Fr0st',wx.YES_NO|wx.CANCEL)
                result = dlg.ShowModal()
                if result == wx.ID_YES:
                    parent = self.tree.GetItemParent(self.TreePanel.item)
                    path = self.tree.GetPyData(parent)
                    self.SaveFlameFile(path, confirm=False)
                elif result == wx.ID_CANCEL:
                    return
                dlg.Destroy()

        self.renderer.exitflag = True      
        self.Destroy()

    @Bind(EVT_IMAGE_READY)
    def OnImageReady(self,e):
        callback, metadata, output_buffer = e.GetValue()
        callback(metadata, output_buffer)


    @Bind(wx.EVT_MENU,id=ID.FOPEN)
    @Bind(wx.EVT_TOOL,id=ID.TBOPEN)
    def OnFlameOpen(self,e):
        dDir,dFile = os.path.split(self.flamepath)
        dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=dDir,
            defaultFile=dFile, wildcard=self.wildcard, style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.flamepath = dlg.GetPath()
            self.OpenFlameFile(self.flamepath)
        dlg.Destroy()


    @Bind(wx.EVT_MENU,id=ID.FSAVE)
    @Bind(wx.EVT_TOOL,id=ID.TBSAVE)
    def OnFlameSave(self,e):
##        if not hasattr(self,"flame"): return
        dDir,dFile = os.path.split(self.flamepath)
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir=dDir, 
            defaultFile=dFile, wildcard=self.wildcard, style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.flamepath = dlg.GetPath()
            self.SaveFlameFile(self.flamepath)
        dlg.Destroy()
        

    @Bind(wx.EVT_MENU,id=ID.SOPEN)
    @Bind(wx.EVT_TOOL,id=ID.TBOPENSCRIPT)
    def OnScriptOpen(self,e):
        # TODO: how can this ugly wrapper be avoided?
        self.editorframe.OnScriptOpen(e)


    @Bind(wx.EVT_TOOL,id=ID.TBRUN)
    def OnRunScript(self,e):
        self.Execute(self.editor.GetText())   


    @Bind(wx.EVT_TOOL,id=ID.TBSTOP)
    def OnStopScript(self,e=None):
        interruptall("Execute")


    @Bind(wx.EVT_TOOL,id=ID.TBEDITOR)
    def OnEditorOpen(self,e):
        self.editorframe.Show(True)
        self.editorframe.SetFocus() # In case it's already open in background

        
    

#------------------------------------------------------------------------------

    def find_open_flame(self,path):
        """Checks if a particular file is open. Returns the file if True,
        None otherwise."""
        root = self.tree.GetRootItem()
        for child in self.TreePanel.iterchildren(root):
            if path == self.tree.GetPyData(child):
                return child


    def OpenFlameFile(self,path):
        # Check if file is already open
        item = self.find_open_flame(path)
        if item:
            self.tree.Delete(item)

        flamestrings = Flame.load_file(path)

        child = self.tree.AppendItem(self.TreePanel.root,os.path.split(path)[1])
        self.tree.SetPyData(child, path)
        self.tree.SetItemImage(child, 0, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(child, 1, wx.TreeItemIcon_Expanded)

        for s in flamestrings:
            item = self.tree.AppendItem(child,self.re_name.findall(s)[0])
            self.tree.SetPyData(item,s)
        self.tree.Expand(child)
        self.tree.SelectItem(child)
        self.TreePanel.RenderThumbnails(child)
        

    def SaveFlameFile(self,path,confirm=True):   
        flamestring = self.flame.to_string()
        found = False

        if os.path.exists(path):
            lst = Flame.load_file(path)
            for i,s in enumerate(lst):
                if self.re_name.findall(s)[0] == self.flame.name:
                    lst[i] = flamestring
                    found = True
                    break
        else:
            lst = []
                
        if not found:
            lst.append(flamestring)
        elif confirm:
            dlg = wx.MessageDialog(self, '%s in %s already exists.\nDo You want to replace it?'
                                   %(self.flame.name,path),
                                   'Fr0st',
                                   wx.YES_NO)
            if dlg.ShowModal() == wx.ID_NO: return
            dlg.Destroy()            
        functions.save_flames(path,*lst)

        # If an open flamefile was modified, it must be reloaded
        if self.find_open_flame(path):
            self.OpenFlameFile(path)

    def SetFlame(self, flame):
        self.flame = flame
        self.image.RenderPreview(flame)
        self.canvas.ShowFlame(flame)

        
    def CreateNamespace(self):
        """Recreates the namespace each time the script is run to reinitialise
        pygame, reassign the flame variable, etc."""
        reload(functions) # calls pygame.init() again
        namespace = dict(self = self, # for debugging only!
                         wx = wx,     # for debugging only!
                         ThreadInterrupt = ThreadInterrupt,
                         GetActiveFlame = self.GetActiveFlame,
                         SetActiveFlame = self.SetActiveFlame,
                         preview = self.preview
                         )

        exec("from lib.functions import *",namespace)
        return namespace


    def PrintScriptStats(self,start):
        print "\nSCRIPT STATS:\n"\
              "Running time %.2f seconds\n" %(time.time()-start)      

    @Threaded
    @XLocked
    @Catches(PyDeadObjectError)
    def Execute(self,string):
        print time.strftime("\n---------- %H:%M:%S ----------")
        start = time.time()

        # split and join fixes linebreak issues between windows and linux
        text = string.splitlines()
        script = "\n".join(text) +'\n'
        self.log._script = text
        
        try:
            self.editor.SetEditable(False)
            # TODO: prevent file opening, etc
            exec(script,self.CreateNamespace())
        except SystemExit:
            pass
        except ThreadInterrupt:
            print("\n\nScript Interrupted")
        finally:
            self.editor.SetEditable(True)
        self.PrintScriptStats(start) # Don't put this in the finally clause!
        

    def GetActiveFlame(self):
        """Returns the flame currently loaded in the GUI. This can't be a
        property because it needs to remain mutable"""
        return self.flame

    def SetActiveFlame(self,flame):
        if not isinstance(flame,Flame):
            raise TypeError("Argument must be an isntance of the Flame class")
        self.flame = flame


    def preview(self):
        # WARNING: This function is called from the script thread, so it's not
        # Allowed to change any shared state.
        self.image.RenderPreview()
        wx.PostEvent(self.canvas, CanvasRefreshEvent())
        time.sleep(.05)


class ImagePanel(wx.Panel):

    @BindEvents
    def __init__(self,parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)
        self.bmp = wx.EmptyBitmap(160,120, 32)
        self.SetMinSize((256,192))


    def RenderPreview(self, flame=None):
        """Renders a preview version of the flame and displays it in the gui.

        Threads are locked outside instead of on the inner render call. This
        allows old requests not correponding to the active flame to be
        discarded."""    
        flame = flame or self.parent.flame

        ratio = flame.size[0] / flame.size[1]
        width = 160 if ratio > 1 else int(160*ratio)
        height = int(width / ratio)
        size = width,height
        req = self.parent.renderer.UrgentRequest
        req(self.UpdateBitmap,size,flame.to_string(),
            size,quality=2,estimator=0,filter=.2)


    def UpdateBitmap(self,size,output_buffer):
        """Callback function to process rendered preview images."""
        width,height = size
        self.bmp = wx.BitmapFromBuffer(width, height, output_buffer)
        self.Refresh()
        # Yield Allows the new image to be drawn immediately.
##        wx.SafeYield()
        wx.Yield()

        
####    @Threaded
##    def RenderPreview(self):
##        self.MakeBitmap(self.parent.flame,strict=True)


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):       
        w,h = self.bmp.GetSize()
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 128-w/2, 96-h/2, True)


