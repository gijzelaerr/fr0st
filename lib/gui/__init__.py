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
from lib.fr0stlib import Flame, BLANKFLAME
from itemdata import ItemData


class MainWindow(wx.Frame):
    re_name = re.compile(r'(?<= name=").*?(?=")') # This re is duplicated!
    wildcard = "Flame file (*.flame)|*.flame|" \
               "All files (*.*)|*.*"

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

        self.flame = None

        # Set up paths
        sys.path.append(os.path.join(sys.path[0],"scripts")) # imp in scripts
        self.flamepath = os.path.join(sys.path[0],"parameters","samples.flame")

        if os.path.exists('paths.temp'):
            # Previous session was interrupted
            # TODO: display a message to user explaining situation.
            paths = [i.strip() for i in open('paths.temp')
                     if os.path.exists(i.strip())]
            self.TreePanel.RecoverSession(paths)
        else:
            # Normal startup
            self.OpenFlame(self.flamepath)

        self.Show(True)
    

#-----------------------------------------------------------------------------
# Event handlers

    @Bind(wx.EVT_MENU,id=ID.ABOUT)
    def OnAbout(self,e):
        d= wx.MessageDialog(self,"......",
                            " TODO", wx.OK)
        d.ShowModal()
        d.Destroy()


    @Bind(wx.EVT_CLOSE)
    @Bind(wx.EVT_MENU,id=ID.EXIT)
    def OnExit(self,e):
        # Give the script editor an opportunity to save.
        self.OnStopScript()
        if self.editorframe.CheckForChanges() == wx.ID_CANCEL:
            return
        
        # check for differences in flame file
        for item in self.TreePanel.iterchildren(self.TreePanel.root):
            if self.CheckForChanges(item) == wx.ID_CANCEL:
                return
            head,ext = os.path.splitext(self.tree.GetPyData(item)[-1])
            path = os.path.join(head + '.temp')
            if os.path.exists(path):
                os.remove(path)

        self.renderer.exitflag = True

        # Remove all temp files
        if os.path.exists('paths.temp'):
            lst = [i.strip()+'.temp' for i in open('paths.temp')]
            for i in lst:
                if os.path.exists(i):
                    os.remove(i)
            os.remove('paths.temp')
        self.Destroy()


    @Bind(EVT_IMAGE_READY)
    def OnImageReady(self,e):
        callback, metadata, output_buffer = e.GetValue()
        callback(metadata, output_buffer)


    @Bind(wx.EVT_MENU,id=ID.FNEW)
    @Bind(wx.EVT_TOOL,id=ID.TBNEW)
    def OnFlameNew(self,e):
        path = 'untitled.flame'
        item = self.TreePanel.NewItem(path)
        self.tree.SelectItem(item)
        
        with open('paths.temp','a') as f:
            f.write(path + '\n')
            

    @Bind(wx.EVT_MENU,id=ID.FNEW2)
    @Bind(wx.EVT_TOOL,id=ID.TBNEW2)
    def OnFlameNew2(self,e):
        name = 'Untitled'
        child = self.tree.AppendItem(self.TreePanel.itemparent, name)
        self.tree.SetPyData(child, ItemData(name, BLANKFLAME))
        self.tree.SelectItem(child)
        self.tree.SetItemImage(child, 2)


    @Bind(wx.EVT_MENU,id=ID.FOPEN)
    @Bind(wx.EVT_TOOL,id=ID.TBOPEN)
    def OnFlameOpen(self,e):
        dDir,dFile = os.path.split(self.flamepath)
        dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=dDir,
            defaultFile=dFile, wildcard=self.wildcard, style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.flamepath = dlg.GetPath()
            self.OpenFlame(self.flamepath)
        dlg.Destroy()


    @Bind(wx.EVT_MENU,id=ID.FSAVE)
    @Bind(wx.EVT_TOOL,id=ID.TBSAVE)
    def OnFlameSave(self,e):
        self.flamepath = self.tree.GetPyData(self.TreePanel.itemparent)[-1]
        dDir,dFile = os.path.split(self.flamepath)
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir=dDir, 
            defaultFile=dFile, wildcard=self.wildcard, style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.flamepath = dlg.GetPath()
            self.SaveFlame(self.flamepath)
        dlg.Destroy()
        
        # Reset the history of all data, to allow correct comparisons.
        for i in self.TreePanel.iterchildren():
            self.tree.GetPyData(i).Reset()
        

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


    @Bind(wx.EVT_TOOL,id=ID.UNDO)
    @Bind(wx.EVT_MENU,id=ID.UNDO)
    def OnUndo(self,e):
        data = self.TreePanel.itemdata
        string = data.Undo()
        if string:
            self.SetFlame(Flame(string=string), rezoom=False)
            self.TreePanel.RenderThumbnail()


    @Bind(wx.EVT_TOOL,id=ID.REDO)
    @Bind(wx.EVT_MENU,id=ID.REDO)
    def OnRedo(self,e):
        data = self.TreePanel.itemdata
        string = data.Redo()
        if string:
            self.SetFlame(Flame(string=string), rezoom=False)
            self.TreePanel.RenderThumbnail()


#------------------------------------------------------------------------------


    def OpenFlame(self,path):
        # Check if file is already open
        item = self.find_open_flame(path)
        if item:
            dlg = wx.MessageDialog(self, "%s is already open. Do you want to revert to its saved status?" % path,
                                   'Fr0st',wx.YES_NO|wx.CANCEL)
            if dlg.ShowModal() != wx.ID_YES:
                return
            self.tree.Delete(item)

        # Create the tree root
        item = self.TreePanel.NewItem(path)

        # Load the file into the tree
        for s in Flame.load_file(path):
            name = self.re_name.findall(s)[0]
            child = self.tree.AppendItem(item, name)
            self.tree.SetPyData(child, ItemData(name, s))
        self.tree.Expand(item)
        self.tree.SelectItem(item)
        self.TreePanel.RenderThumbnails(item)

        # Dump the path to file for bookkeeping
        with open('paths.temp','a') as f:
            f.write(path + '\n')        
        

    def SaveFlame(self, path, item=None, confirm=True):
        # Refuse to save if file is open
        data = self.tree.GetPyData(self.TreePanel.itemparent)
        if data[-1] != path and self.find_open_flame(path):
            dlg = wx.MessageDialog(self, "%s is currently open. Please choose a different name." % path,
                                   'Fr0st',wx.OK)
            dlg.ShowModal()
            return

        # Check if we're overwriting anything
        if os.path.exists(path) and confirm:
            dlg = wx.MessageDialog(self, '%s already exists.\nDo You want to replace it?'
                                   %path,
                                   'Fr0st',
                                   wx.YES_NO)
            if dlg.ShowModal() == wx.ID_NO: return
            dlg.Destroy()

        # Now update the tree items
        self.tree.SetItemText(self.TreePanel.itemparent, os.path.basename(path))
        data[-1] = path
                      
        lst = []
        for i in self.TreePanel.iterchildren(item):
            data = self.tree.GetPyData(i)
            lst.append(data.GetSaveString())
            self.tree.SetItemText(i, data.name)
        
        # Finally, save the flame and clear the temp file.
        functions.save_flames(path,*lst)
        if os.path.exists(path+'.temp'):
            os.remove(path+'.temp')

        self.tree.SelectItem(self.TreePanel.itemparent)


    def find_open_flame(self,path):
        """Checks if a particular file is open. Returns the file if True,
        None otherwise."""
        root = self.tree.GetRootItem()
        for child in self.TreePanel.iterchildren(root):
            if path == self.tree.GetPyData(child)[-1]:
                return child


    def CheckForChanges(self,item):
        if any(self.tree.GetPyData(child).HasChanged()
               for child in self.TreePanel.iterchildren(item)):
            path = self.tree.GetPyData(item)[-1]
            dlg = wx.MessageDialog(self, 'Save changes to %s?' % path,
                                   'Fr0st',wx.YES_NO|wx.CANCEL)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                self.SaveFlame(path, item, confirm=False)
            dlg.Destroy()
            return result


    def EnableUndo(self,flag):
        self.tb.EnableTool(ID.UNDO,bool(flag))
        # TODO: same with the menu option


    def EnableRedo(self,flag):
        self.tb.EnableTool(ID.REDO,bool(flag))
        # TODO: same with the menu option

        
    def SetFlame(self, flame, rezoom=True):
        self.flame = flame
        self.image.RenderPreview(flame)
        self.canvas.ShowFlame(flame,rezoom=rezoom)

        # Set Undo and redo buttons to the correct value:
        data = self.TreePanel.itemdata
        self.EnableUndo(data.undo)
        self.EnableRedo(data.redo)

        
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
        time.sleep(.05) # Avoids spamming too many requests.


class ImagePanel(wx.Panel):

    @BindEvents
    def __init__(self,parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)
        self.bmp = wx.EmptyBitmap(160,120, 32)
        self.SetMinSize((256,192))


    def RenderPreview(self, flame=None):
        """Renders a preview version of the flame and displays it in the gui.

        The renderer takes care of denying repeated requests so that at most
        one redundant preview is rendered."""    
        flame = flame or self.parent.flame

        ratio = flame.size[0] / flame.size[1]
        width = 160 if ratio > 1 else int(160*ratio)
        height = int(width / ratio)
        size = width,height
        req = self.parent.renderer.UrgentRequest
        req(self.UpdateBitmap,size,flame.to_string(),
            size,quality=2,estimator=0,filter=.2)


##    @XLocked
    def UpdateBitmap(self,size,output_buffer):
        """Callback function to process rendered preview images."""
        width,height = size
        self.bmp = wx.BitmapFromBuffer(width, height, output_buffer)
        self.Refresh()
        # Removed the Yield call because it opened the door to infinite
        # recursion. It seems to have been unneeded anyway.
##        wx.SafeYield()
##        wx.Yield()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):       
        w,h = self.bmp.GetSize()
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 128-w/2, 96-h/2, True)


