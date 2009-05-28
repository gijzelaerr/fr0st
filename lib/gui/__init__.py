from __future__ import with_statement
import os, sys, wx, time, re, threading, itertools
from wx import PyDeadObjectError

from lib.gui.scripteditor import EditorFrame
from lib.gui.preview import PreviewFrame
from lib.gui.filetree import TreePanel
from lib.gui.menu import CreateMenu
from lib.gui.toolbar import CreateToolBar
from lib.gui.decorators import *
from lib.gui.constants import ID
##from lib.gui.canvas import XformCanvas
from lib.gui.gradient import MainNotebook
from lib.gui.xformeditor import XformTabs
from lib.threadinterrupt import interruptall
from lib._exceptions import ThreadInterrupt
from lib import fr0stlib
from lib.pyflam3 import Genome
from lib.gui.rendering import render, Renderer
from lib.gui._events import EVT_THREAD_MESSAGE, ThreadMessageEvent
from lib.fr0stlib import Flame, BLANKFLAME
from itemdata import ItemData


class MainWindow(wx.Frame):
    wildcard = "Flame file (*.flame)|*.flame|" \
               "All files (*.*)|*.*"
    newfilename = ("Untitled%s.flame" % i for i in itertools.count(1)).next
    scriptrunning = False


    @BindEvents
    def __init__(self,parent,id):
        self.title = "Fractal Fr0st"
        wx.Frame.__init__(self,parent,wx.ID_ANY, self.title)    

        # This icon stuff is not working...
##        ib=wx.IconBundle()
##        ib.AddIconFromFile("Icon.ico",wx.BITMAP_TYPE_ANY)
##        self.SetIcons(ib)
        self.CreateStatusBar()
        self.SetMinSize((750,500))
        self.SetDoubleBuffered(True)
        
        # Launch the render thread
        self.renderer = Renderer(self)
        
        # Creating Frame Content
        CreateMenu(self)
        CreateToolBar(self)
        self.image = ImagePanel(self)
##        self.grad = GradientPanel(self)
        self.XformTabs = XformTabs(self)
##        self.canvas = XformCanvas(self)
        self.notebook = MainNotebook(self)
        self.grad = self.notebook.grad
        self.canvas = self.notebook.canvas

        self.previewframe = PreviewFrame(self)

        self.editorframe = EditorFrame(self)
        self.editor = self.editorframe.editor
        self.log = self.editorframe.log 
        
        self.TreePanel = TreePanel(self)
        self.tree = self.TreePanel.tree

        sizer3 = wx.BoxSizer(wx.VERTICAL)
##        sizer3.Add(self.grad,0,wx.ALIGN_CENTER_HORIZONTAL)
##        sizer3.Add(self.canvas,1,wx.EXPAND)
        sizer3.Add(self.notebook,1,wx.EXPAND)

        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.image,0,wx.EXPAND)
        sizer2.Add(self.XformTabs.Selector,0)
        sizer2.Add(self.XformTabs,1,wx.EXPAND)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.TreePanel,0,wx.EXPAND)
        sizer.Add(sizer3,1,wx.EXPAND)
##        sizer.Add(self.canvas,1,wx.EXPAND)
        sizer.Add(sizer2,0,wx.EXPAND)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(1)

        sizer.Fit(self)

##        self.SetSize((800,600))

        self.flame = Flame(string=fr0stlib.BLANKFLAME)

        # Set up paths
        sys.path.append(os.path.join(sys.path[0],"scripts")) # imp in scripts
        self.flamepath = os.path.join(sys.path[0],"parameters","samples.flame")
        
        if os.path.exists('paths.temp') and False:
            # TODO: check if another fr0st process is running.
            # Previous session was interrupted
            # TODO: display a message to user explaining situation.
            paths = [i.strip() for i in open('paths.temp')]
            self.TreePanel.RecoverSession(paths)

        else:
            # Normal startup
            self.tree.item = self.OpenFlame(self.flamepath)
            
##        self.tree.ExpandAll()
        self.tree.SelectItem(self.tree.GetItemByIndex((0,0)))

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
        for itemdata,lst in self.tree.flamefiles:
            if self.CheckForChanges(itemdata, lst) == wx.ID_CANCEL:
                return
            head,ext = os.path.splitext(itemdata[-1])
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


    @Bind(EVT_THREAD_MESSAGE)
    def OnImageReady(self,e):
        callback, metadata, output_buffer = e.GetValue()
        callback(metadata, output_buffer)


    @Bind(wx.EVT_MENU,id=ID.FNEW)
    @Bind(wx.EVT_TOOL,id=ID.TBNEW)
    def OnFlameNew(self,e):
        path = self.newfilename()
        item = self.tree.AddFlamefile(path, [])
        self.tree.SelectItem(item)
        
        with open('paths.temp','a') as f:
            f.write(path + '\n')
            
        return item
            

    @Bind(wx.EVT_MENU,id=ID.FNEW2)
    @Bind(wx.EVT_TOOL,id=ID.TBNEW2)
    def OnFlameNew2(self,e):
        data = ItemData(BLANKFLAME)

        index = self.tree.GetIndexOfItem(self.tree.itemparent)
        self.tree.GetChildren(index).append((data,[]))

        self.tree.RefreshItems()
        child = self.tree.GetItemByIndex(index + (-1,))
        self.tree.SelectItem(child)

        # This adds the flame to the temp file, but without any actual changes.
        data.pop(0)
        self.TreePanel.TempSave()

        return child


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
        self.flamepath = self.tree.GetFlameData(self.tree.itemparent)[-1]
        self.SaveFlame(self.flamepath, confirm=False)

        
    @Bind(wx.EVT_MENU,id=ID.FSAVEAS)
    @Bind(wx.EVT_TOOL,id=ID.TBSAVEAS)
    def OnFlameSaveAs(self,e):
        self.flamepath = self.tree.GetFlameData(self.tree.itemparent)[-1]
        dDir,dFile = os.path.split(self.flamepath)
        dlg = wx.FileDialog(self, message="Save file as ...", defaultDir=dDir,
                            defaultFile=dFile, wildcard=self.wildcard,
                            style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.flamepath = dlg.GetPath()
            self.SaveFlame(self.flamepath)
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
        self.editorframe.Raise()
        self.editorframe.SetFocus() # In case it's already open in background


    @Bind(wx.EVT_TOOL, id=ID.TBPREVIEW)
    def OnPreviewOpen(self, e):
        self.previewframe.Show(True)
        self.previewframe.Raise()
        self.previewframe.RenderPreview()


    @Bind(wx.EVT_TOOL,id=ID.UNDO)
    @Bind(wx.EVT_MENU,id=ID.UNDO)
    def OnUndo(self,e):
        data = self.tree.itemdata
        string = data.Undo()
        if string:
            self.SetFlame(Flame(string=string), rezoom=False)
            self.tree.RenderThumbnail()
            self.tree.SetItemText(self.tree.item, data.name)


    @Bind(wx.EVT_TOOL,id=ID.REDO)
    @Bind(wx.EVT_MENU,id=ID.REDO)
    def OnRedo(self,e):
        data = self.tree.itemdata
        string = data.Redo()
        if string:
            self.SetFlame(Flame(string=string), rezoom=False)
            self.tree.RenderThumbnail()
            self.tree.SetItemText(self.tree.item, data.name)


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

        # scan the file to see if it's valid
        flamestrings = Flame.load_file(path)
        if not flamestrings:
            dlg = wx.MessageDialog(self, "It seems %s is not a valid flame file. Please choose a different flame." % path,
                                   'Fr0st',wx.OK)
            dlg.ShowModal()
            self.OnFlameOpen(None)
            return

        # Add flames to the tree
        self.tree.AddFlamefile(path, flamestrings)

        # Dump the path to file for bookkeeping
        with open('paths.temp','a') as f:
            f.write(path + '\n')

        return item
        

    def SaveFlame(self, path, confirm=True):
        # Refuse to save if file is open
        data = self.tree.GetFlameData(self.tree.itemparent)
        if data[-1] != path and self.find_open_flame(path):
            dlg = wx.MessageDialog(self, "%s is currently open. Please choose a different name." % path,
                                   'Fr0st',wx.OK)
            dlg.ShowModal()
            return

        # Check if we're overwriting anything
        if os.path.exists(path) and confirm:
            dlg = wx.MessageDialog(self, '%s already exists.\nDo You want to replace it?'
                                   %path, 'Fr0st', wx.YES_NO)
            if dlg.ShowModal() == wx.ID_NO: return
            dlg.Destroy()

        # Now update the tree items
        self.tree.SetItemText(self.tree.itemparent, os.path.basename(path))
        data[-1] = path
                      
        lst = []
        for i in self.tree.GetItemChildren():
            data = self.tree.GetFlameData(i)
            lst.append(data.GetSaveString())

            # Reset the history of all data, to allow correct comparisons.
            data.Reset()
            self.tree.SetItemText(i, data.name)
        
        # Finally, save the flame and clear the temp file.
        fr0stlib.save_flames(path,*lst)
        if os.path.exists(path+'.temp'):
            os.remove(path+'.temp')

        self.tree.SelectItem(self.tree.itemparent)


    def find_open_flame(self,path):
        """Checks if a particular file is open. Returns the file if True,
        None otherwise."""
        for child in self.tree.GetItemChildren(self.tree.root):
            if path == self.tree.GetFlameData(child)[-1]:
                return child


    def CheckForChanges(self, itemdata, lst):
        if any(data.HasChanged() for data,_ in lst):
            path = itemdata[-1]
            dlg = wx.MessageDialog(self, 'Save changes to %s?' % path,
                                   'Fr0st',wx.YES_NO|wx.CANCEL)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                fr0stlib.save_flames(path, *(data.GetSaveString()
                                             for data,_ in lst))
            dlg.Destroy()
            return result


    def EnableUndo(self,flag):        
        self.tb.EnableTool(ID.UNDO,bool(flag))
        # TODO: same with the menu option


    def EnableRedo(self,flag):
        self.tb.EnableTool(ID.REDO,bool(flag))
        # TODO: same with the menu option


    @CallableFrom('MainThread')
    def SetFlame(self, flame, rezoom=True):
        """Changes the active flame and updates all relevant widgets.
        This function can only be called from the main thread, because wx is
        not thread-safe under linux (wxgtk)."""
        self.flame = flame
        if not self.ActiveXform:
            self.ActiveXform = flame.xform[0]
        elif self.ActiveXform._parent != flame:
            index = min(self.ActiveXform.index, len(flame.xform)-1)
            self.ActiveXform = flame.xform[index]
            
        self.image.RenderPreview(flame)
        self.large_preview()
        self.canvas.ShowFlame(flame,rezoom=rezoom)
        self.grad.OnUpdate()
        self.XformTabs.UpdateView()

        # Set Undo and redo buttons to the correct value:
        data = self.tree.itemdata
        self.EnableUndo(data.undo)
        self.EnableRedo(data.redo)

        
    def CreateNamespace(self):
        """Recreates the namespace each time the script is run to reinitialise
        pygame, reassign the flame variable, etc."""
        namespace = dict(self = self, # for debugging only!
                         wx = wx,     # for debugging only!
                         ThreadInterrupt = ThreadInterrupt,
                         GetActiveFlame = self.GetActiveFlame,
                         SetActiveFlame = self.SetActiveFlame,
                         preview = self.preview,
                         large_preview = self.large_preview)

        exec("from lib.fr0stlib import *; __name__='__main__'",namespace)
        return namespace


    def PrintScriptStats(self,start):
        print "\nSCRIPT STATS:\n"\
              "Running time %.2f seconds\n" %(time.time()-start)      

    @Threaded
    @Locked(blocking=False)
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
            self.scriptrunning = True
            # TODO: prevent file opening, etc
            exec(script,self.CreateNamespace())
        except SystemExit:
            pass
        except ThreadInterrupt:
            print("\n\nScript Interrupted")
        finally:
            self.editor.SetEditable(True)
            self.scriptrunning = False
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
        wx.PostEvent(self.canvas, ThreadMessageEvent())
        wx.PostEvent(self.grad, ThreadMessageEvent())
        time.sleep(.05) # Avoids spamming too many requests.

    def large_preview(self):
        if self.previewframe.IsShown():
            self.previewframe.RenderPreview()


class ImagePanel(wx.Panel):

    @BindEvents
    def __init__(self,parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)
        self.bmp = wx.EmptyBitmap(160,120, 32)
        self.SetMinSize((256, 192))


    def RenderPreview(self, flame=None):
        """Renders a preview version of the flame and displays it in the gui.

        The renderer takes care of denying repeated requests so that at most
        one redundant preview is rendered."""    
        flame = flame or self.parent.flame

        ratio = flame.size[0] / flame.size[1]
        width = 160 if ratio > 1 else int(160*ratio)
        height = int(width / ratio)
        size = width,height
        req = self.parent.renderer.PreviewRequest
        req(self.UpdateBitmap,size,flame.to_string(),
            size,quality=2,estimator=0,filter=.2)


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

