from __future__ import with_statement
import os, sys, wx, time, re, threading, itertools
from wx import PyDeadObjectError

from lib.gui.scripteditor import EditorFrame
from lib.gui.preview import PreviewFrame, PreviewBase
from lib.gui.filetree import TreePanel
from lib.gui.menu import CreateMenu
from lib.gui.toolbar import CreateToolBar
from lib.gui.constants import ID
from lib.gui.maineditor import MainNotebook
from lib.gui.xformeditor import XformTabs
from lib.gui.renderer import Renderer
from lib.gui._events import EVT_THREAD_MESSAGE, ThreadMessageEvent
from lib.gui.itemdata import ItemData
from lib.gui.renderdialog import RenderDialog
from lib.gui.config import config

from lib import fr0stlib
from lib.fr0stlib import Flame, BLANKFLAME
from lib.pyflam3 import Genome
from lib.decorators import *
from lib.threadinterrupt import ThreadInterrupt, interruptall

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
        self.SetDoubleBuffered(True)
        
        # Launch the render thread
        self.renderer = Renderer(self)
        self.renderdialog = None
        
        # Creating Frame Content
        CreateMenu(parent=self)
        CreateToolBar(self)
        self.image = ImagePanel(self)
        self.XformTabs = XformTabs(self)
        self.notebook = MainNotebook(self)
        self.grad = self.notebook.grad
        self.canvas = self.notebook.canvas
        self.adjust = self.notebook.adjust

        self.previewframe = PreviewFrame(self)

        self.editorframe = EditorFrame(self)
        self.editor = self.editorframe.editor
        self.log = self.editorframe.log 
        
        self.TreePanel = TreePanel(self)
        self.tree = self.TreePanel.tree

        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer3.Add(self.notebook,1,wx.EXPAND)

        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.image,0,wx.EXPAND)
        sizer2.Add(self.XformTabs.Selector,0)
        sizer2.Add(self.XformTabs,1,wx.EXPAND)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.TreePanel,0,wx.EXPAND)
        sizer.Add(sizer3,1,wx.EXPAND)
        sizer.Add(sizer2,0,wx.EXPAND)
        
        self.SetSizer(sizer)

        # Calculate the correct minimum size dynamically.
        sizer.Fit(self)
        self.SetMinSize(self.GetSize())
        
        # Load frame positions from file
        for window, k in ((self, "Rect-Main"),
                          (self.editorframe, "Rect-Editor"),
                          (self.previewframe, "Rect-Preview")):
            if k in config:
                rect, maximize = config[k]
                window.SetDimensions(*rect)
                window.Maximize(maximize)

        self._namespace = self.CreateNamespace()

        # Set up paths
        sys.path.append(os.path.join(sys.path[0],"scripts")) # imp in scripts
        self.flamepath = os.path.join(sys.path[0], config["flamepath"])
        
        if os.path.exists('paths.temp') and False:
            # TODO: check if another fr0st process is running.
            # Previous session was interrupted
            # TODO: display a message to user explaining situation.
            paths = [i.strip() for i in open('paths.temp')]
            self.TreePanel.RecoverSession(paths)

        else:
            # Normal startup
            try:
                self.tree.item = self.OpenFlame(self.flamepath)
            except:
                self.OnFlameNew(e=None)
##                self.OnFlameNew2(e=None)
            
##        self.tree.ExpandAll()
        self.tree.SelectItem(self.tree.GetItemByIndex((0,0)))

        self.Enable(ID.STOP, False, editor=True)
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
        # check for renders in progress
        if self.renderdialog and self.renderdialog.OnExit() == wx.ID_NO:
            return
            
        # check for script diffs
        self.OnStopScript()
        if self.editorframe.CheckForChanges() == wx.ID_CANCEL:
            return
        
        # check for flame diffs
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

        # Save size and pos of each window
        for window, k in ((self, "Rect-Main"),
                          (self.editorframe, "Rect-Editor"),
                          (self.previewframe, "Rect-Preview")):
            maximize = window.IsMaximized()
            # HACK: unmaximizing doesn't seem to work properly in this context,
            # so we just use the previous config settings, even if it's not
            # ideal.
##            window.Maximize(False)
            if maximize:
                (x,y,w,h), _ = config[k]
            else:
                x,y = window.GetPosition()
                w,h = window.GetSize()
            config[k] = (x,y,w,h), maximize
        self.Destroy()


##    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FNEW)
    def OnFlameNew(self, e):
        path = self.newfilename()
        self.tree.item = self.tree.AddFlamefile(path, [])
        
        with open('paths.temp','a') as f:
            f.write(path + '\n')
            
        return self.tree.item
            

    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FNEW2)
    def OnFlameNew2(self,e):
        data = ItemData(BLANKFLAME)

        self.tree.GetChildren((0,)).append((data,[]))
        self.tree.RefreshItems()
        
        # This is needed to avoid an indexerror when getting child.
        self.tree.Expand(self.tree.itemparent)
        
        child = self.tree.GetItemByIndex((0, -1))
        self.tree.SelectItem(child)

        # This adds the flame to the temp file, but without any actual changes.
        data.pop(0)
        self.TreePanel.TempSave()

        return child


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FOPEN)
    def OnFlameOpen(self,e):
        dDir,dFile = os.path.split(self.flamepath)
        dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=dDir,
            defaultFile=dFile, wildcard=self.wildcard, style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.flamepath = dlg.GetPath()
            self.OpenFlame(self.flamepath)
        dlg.Destroy()


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FSAVE)
    def OnFlameSave(self,e):
        self.flamepath = self.tree.GetFlameData(self.tree.itemparent)[-1]
        self.SaveFlame(self.flamepath, confirm=False)

        
    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FSAVEAS)
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
        

    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.SOPEN)
    def OnScriptOpen(self,e):
        # TODO: how can this ugly wrapper be avoided?
        self.editorframe.OnScriptOpen(e)


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.RUN)
    def OnRunScript(self,e):
        self.BlockGUI(flag=True)
        self.Execute(self.editor.GetText())


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.STOP)
    def OnStopScript(self,e=None):
        interruptall("Execute")


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.EDITOR)
    def OnEditorOpen(self,e):
        self.editorframe.Show(True)
        self.editorframe.Raise()
        self.editorframe.SetFocus() # In case it's already open in background


    @Bind(wx.EVT_TOOL, id=ID.PREVIEW)
    def OnPreviewOpen(self, e):
        self.previewframe.Show(True)
        self.previewframe.Raise()
        self.previewframe.RenderPreview()      


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.UNDO)
    def OnUndo(self,e):
        data = self.tree.itemdata
        self.SetFlame(Flame(string=data.Undo()), rezoom=False)
        self.tree.RenderThumbnail()
        self.tree.SetItemText(self.tree.item, data.name)

            
    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.UNDOALL)
    def OnUndoAll(self, e):
        data = self.tree.itemdata
        self.SetFlame(Flame(string=data.UndoAll()), rezoom=False)
        self.tree.RenderThumbnail()
        self.tree.SetItemText(self.tree.item, data.name)    


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.REDO)
    def OnRedo(self,e):
        data = self.tree.itemdata
        self.SetFlame(Flame(string=data.Redo()), rezoom=False)
        self.tree.RenderThumbnail()
        self.tree.SetItemText(self.tree.item, data.name)

            
    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.REDOALL)
    def OnRedoAll(self,e):
        data = self.tree.itemdata
        self.SetFlame(Flame(string=data.RedoAll()), rezoom=False)
        self.tree.RenderThumbnail()
        self.tree.SetItemText(self.tree.item, data.name)


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.RENDER)
    def OnRender(self,e):
        if self.renderdialog:
            self.renderdialog.Raise()
        else:
            self.renderdialog = RenderDialog(self, ID.RENDER)

#------------------------------------------------------------------------------    

    def OpenFlame(self, path):
        if self.tree.flamefiles:
            filedata, lst = self.tree.flamefiles[0]
            if path == filedata[-1]:
                # File is already open
                dlg = wx.MessageDialog(self, "%s is already open. Do you want to revert to its saved status?" % path,
                                       'Fr0st',wx.YES_NO|wx.CANCEL)
                if dlg.ShowModal() != wx.ID_YES:
                    return
            elif self.CheckForChanges(filedata, lst) == wx.ID_CANCEL:
                # User cancelled when prompted to save changes.
                return

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


    def SaveFlame(self, path, confirm=True):
        lst = Flame.load_file(path) if os.path.exists(path) else []
            
        if self.tree.parentselected:
            itr = (i for i,_ in self.tree.flamefiles[0][1])
        else:
            itr = (self.tree.itemdata,)
        for i, data in enumerate(itr):
            index = lst.index(data[0])
            if data[0] in lst:
                lst[index] = data[-1]
            else:
                lst.append(data[-1])

            data.Reset()
            self.tree.SetItemText(self.tree.GetItemByIndex((0,index)),
                                  data.name)

        fr0stlib.save_flames(path,*lst)
        

    def CheckForChanges(self, itemdata, lst):
        if any(data.HasChanged() for data,_ in lst):
            path = itemdata[-1]
            dlg = wx.MessageDialog(self, 'Save changes to %s?' % path,
                                   'Fr0st',wx.YES_NO|wx.CANCEL)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                fr0stlib.save_flames(path, *(data[-1] for data,_ in lst))
            dlg.Destroy()
            return result


    @Bind(EVT_THREAD_MESSAGE, id=ID.ENDOFSCRIPT)
    def EndOfScript(self, e):
        self.BlockGUI(False)
        # Check if flame has changed to see if tempsave is needed. to_string
        # is necessary to detect identical flames saved in different apps.
        # all conversions together might take about 5ms.
        string = self.tree.itemdata[-1]
        if Flame(string=string).to_string() != self.flame.to_string():
            self.TreePanel.TempSave()

        
    @CallableFrom('MainThread')
    def BlockGUI(self, flag=False):
        """Called before and after a script runs."""
        # TODO: prevent file opening, etc
        self.Enable(ID.RUN, not flag, editor=True)
        self.Enable(ID.STOP, flag, editor=True)
        self.editor.SetEditable(not flag)
        self.scriptrunning = flag


    @CallableFrom('MainThread')
    def Enable(self, id, flag, editor=False):
        """Enables/Disables toolbar and menu items."""
        flag = bool(flag)
        self.tb.EnableTool(id, flag)
        self.menu.Enable(id, flag)
        if editor:
            self.editorframe.tb.EnableTool(id, flag)
            

    @CallableFrom('MainThread')
    def SetFlame(self, flame, rezoom=True):
        """Changes the active flame and updates all relevant widgets.
        This function can only be called from the main thread, because wx is
        not thread-safe under linux (wxgtk)."""
        self.flame = flame
        if not self.ActiveXform:
            self.ActiveXform = flame.xform[0]
        elif self.ActiveXform._parent != flame:
            if self.ActiveXform.index == None:
                self.ActiveXform = flame.final or flame.xform[0]
            else:
                index = min(self.ActiveXform.index, len(flame.xform)-1)
                self.ActiveXform = flame.xform[index]
            
        self.image.RenderPreview(flame)
        self.large_preview()
        self.XformTabs.UpdateView()
        self.notebook.UpdateView(rezoom=rezoom)

        # Set Undo and redo buttons to the correct value:
        data = self.tree.itemdata
        self.Enable(ID.UNDOALL, data.undo)
        self.Enable(ID.UNDO, data.undo)
        self.Enable(ID.REDO, data.redo)
        self.Enable(ID.REDOALL, data.redo)

        
    def CreateNamespace(self):
        """Recreates the namespace each time the script is run to reassign
        the flame variable, etc."""
        namespace = dict(self = self, # for debugging only!
                         flame = Flame(string=fr0stlib.BLANKFLAME),
                         get_flames = self.tree.GetFlames,
                         preview = self.preview,
                         large_preview = self.large_preview,
                         dialog = self.editorframe.make_dialog,
                         )

        exec("from lib.fr0stlib import *; __name__='__main__'",namespace)
        return namespace


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
            exec(script,self._namespace)
        except SystemExit:
            pass
        except ThreadInterrupt:
            print("\n\nScript Interrupted")
        finally:
            # This lets the GUI know that the script has finished.
            wx.PostEvent(self, ThreadMessageEvent(ID.ENDOFSCRIPT))

        # Keep this out of the finally clause!
        print "\nSCRIPT STATS:\n"\
              "Running time %.2f seconds\n" %(time.time()-start)


    @property
    def flame(self):
        return self._namespace['flame']
    @flame.setter
    def flame(self, flame):
        if not isinstance(flame,Flame):
            raise TypeError("Argument must be a Flame object")
        self._namespace['flame'] = flame


    def preview(self):
        # WARNING: This function is called from the script thread, so it's not
        # Allowed to change any shared state.
        self.image.RenderPreview()
        wx.PostEvent(self, ThreadMessageEvent(ID.PREVIEW))
        time.sleep(.05) # Avoids spamming too many requests.


    def large_preview(self):
        if self.previewframe.IsShown():
            self.previewframe.RenderPreview()


    @Bind(EVT_THREAD_MESSAGE, id=ID.PREVIEW)
    def OnPreview(self, e):
        # only update a select few of all the panels.
        # TODO: need to test if this is really necessary.
##        self.XformTabs.UpdateView()
##        self.notebook.UpdateView()
        self.canvas.ShowFlame(rezoom=False)
        self.grad.UpdateView()


    @Bind(EVT_THREAD_MESSAGE, id=ID.RENDER)
    def OnImageReady(self,e):
        callback, (w,h), output_buffer, channels = e.GetValue()
        if channels == 3:
            fun = wx.BitmapFromBuffer
        elif channels == 4:
            fun = wx.BitmapFromBufferRGBA
        else:
            raise ValueError("need 3 or 4 channels, not %s" % channels)
        callback(fun(w, h, output_buffer))        



class ImagePanel(PreviewBase):

    @BindEvents
    def __init__(self, parent):
        self.parent = parent
        # HACK: we change the class temorarily so the BindEvents decorator
        # catches the methods in the base class.
        self.__class__ = PreviewBase
        PreviewBase.__init__(self, parent)
        self.__class__ = ImagePanel
        self.SetSize((256, 220))
        self.bmp = wx.EmptyBitmap(400,300, 32)


    def GetPanelSize(self):
        return self.Size
    

    def RenderPreview(self, flame=None):
        """Renders a preview version of the flame and displays it in the gui.

        The renderer takes care of denying repeated requests so that at most
        one redundant preview is rendered."""    
        flame = flame or self.parent.flame

        ratio = flame.size[0] / flame.size[1]
        width = 200 if ratio > 1 else int(200*ratio)
        height = int(width / ratio)
        size = width,height
        self.parent.renderer.PreviewRequest(self.UpdateBitmap, flame, size,
                                            **config["Preview-Settings"])


    def UpdateBitmap(self, bmp):
        """Callback function to process rendered preview images."""
        self.bmp = bmp
        self.Refresh()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):       
        fw,fh = self.bmp.GetSize()
        pw,ph = self.GetPanelSize()
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, (pw-fw) / 2, (ph-fh) / 2, True)

