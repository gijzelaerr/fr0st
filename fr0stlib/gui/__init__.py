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
import imp, os, sys, wx, time, shutil
from copy import deepcopy

from fr0stlib.gui.scripteditor import EditorFrame
from fr0stlib.gui.preview import PreviewFrame, PreviewBase
from fr0stlib.gui.filetree import TreePanel
from fr0stlib.gui.menu import CreateMenu
from fr0stlib.gui.toolbar import CreateToolBar
from fr0stlib.gui.constants import ID
from fr0stlib.gui.maineditor import MainNotebook
from fr0stlib.gui.xformeditor import XformTabs
from fr0stlib.gui.renderer import Renderer
from fr0stlib.gui._events import InMain
from fr0stlib.gui.itemdata import ItemData
from fr0stlib.gui.renderdialog import RenderDialog
from fr0stlib.gui.config import config, init_config
from fr0stlib.gui.configdlg import ConfigDialog
from fr0stlib.gui.filedialogs import SaveDialog, NewFileDialog
from fr0stlib.gui.exceptiondlg import unhandled_exception_handler
from fr0stlib.pyflam3.cuda import is_cuda_capable

import fr0stlib
from fr0stlib import Flame, save_flames
from fr0stlib.pyflam3 import Genome
from fr0stlib.decorators import *
from fr0stlib.threadinterrupt import ThreadInterrupt, interruptall

# Don't write .pyc files to keep script folder clean
sys.dont_write_bytecode = True

# Let scripts know that they're being run in a graphical environment.
fr0stlib.GUI = True


class Fr0stApp(wx.App):
    def __init__(self):
        wx.App.__init__(self, redirect=False)
        self.SetAppName('fr0st')
        self.standard_paths = wx.StandardPaths.Get()
        
        # AppBaseDir needs to be set before any path manipulation so abspath
        # works as expected.
        if self.Frozen:
            self.AppBaseDir = os.path.abspath(os.path.dirname(sys.executable))
        else:
            self.AppBaseDir = os.path.abspath(os.path.dirname(sys.argv[0]))
        
        if 'win32' in sys.platform:
            # On windows, GetResourcesDir returns something like
            #   "c:\Python26\lib\site-packages\wx-2.8-msw-unicode\wx\"
            # Grab the base directory instead
            self.resource_dir = self.AppBaseDir
        else:
            self.resource_dir = self.standard_paths.GetResourcesDir()

        self.CreateUserDirectory()

        # set the cwd to user dir so relative paths will work as expected and
        # not depend on the platform.
        os.chdir(self.user_dir)

        # Put the config file into the same folder where everything else is.
##        self.config_dir = os.path.join(self.standard_paths.GetUserConfigDir(),
##                                       '.fr0st')
        self.config_dir = self.user_dir

        if not os.path.exists(self.ConfigDir):
            os.makedirs(self.ConfigDir)

        init_config()

        if config['renderer'] == 'flam4' and not is_cuda_capable():
            config['renderer'] = 'flam3'


    def CreateUserDirectory(self):
        self.user_dir = self.standard_paths.GetDocumentsDir()

        # On *nix, GetDocumentsDir returns ~.  use .fr0st rather than fr0st
        if os.path.realpath(os.path.expanduser('~')) == os.path.realpath(self.user_dir):
            self.user_dir = os.path.join(self.user_dir, '.fr0st')
        else:
            self.user_dir = os.path.join(self.user_dir, 'fr0st')

        # Create the user directory
        if not os.path.exists(self.user_dir):
            os.makedirs(self.user_dir)

        # make sure renders subdirectory exists
        if not os.path.exists(self.RendersDir):
            os.makedirs(self.RendersDir)

        # Find out where we need to copy from
        basepath = self.AppBaseDir

        if not os.path.exists(os.path.join(basepath, 'parameters')):
            # installed, copy from /usr/share/.... or whatever
            basepath = self.resource_dir

        def mirror_directory(source, dest, directory):
            """Mirror all files and directories in source/directory to dest/directory"""

            # Ensure destination path exists
            if not os.path.exists(os.path.join(dest, directory)):
                os.makedirs(os.path.join(dest, directory))

            # get the list of files and folders
            source_all = [ x for x in os.listdir(os.path.join(source, directory)) ]
            source_files = [ x for x in source_all if os.path.isfile(os.path.join(source, directory, x)) ]
            source_dirs = [ x for x in source_all if os.path.isdir(os.path.join(source, directory, x)) ]

            for file in source_files:
                # Skip it if it's already there
                if os.path.exists(os.path.join(dest, directory, file)):
                    continue

                # Otherwise copy it over
                shutil.copy(os.path.join(source, directory, file), os.path.join(dest, directory))

            # Recurse into subdirectories
            for child_dir in source_dirs:
                mirror_directory(source, dest, os.path.join(directory, child_dir))

        # Mirror app standard scripts/parameters to user dir
        mirror_directory(basepath, self.user_dir, 'parameters')
        mirror_directory(basepath, self.user_dir, 'scripts')

    def MainLoop(self):
        single_instance_name = 'fr0st-%s' % wx.GetUserId()
        single_instance = wx.SingleInstanceChecker(single_instance_name)

        if single_instance.IsAnotherRunning():
            wx.MessageDialog(None, "Another instance of fr0st is already "
                             "running. Multiple instances are not supported.",
                             "fr0st", wx.OK|wx.ICON_ERROR).ShowModal()
            return

        MainWindow(None, wx.ID_ANY)
        wx.App.MainLoop(self)

    @property
    def UserParametersDir(self):
        return os.path.join(self.user_dir, 'parameters')

    @property
    def RendersDir(self):
        return os.path.join(self.user_dir, 'renders')

    @property
    def UserScriptsDir(self):
        return os.path.join(self.user_dir, 'scripts')

    @property
    def ConfigDir(self):
        return self.config_dir

    @property
    def Frozen(self):
        return (hasattr(sys, 'frozen') or
                hasattr(sys, 'importers') or
                imp.is_frozen('__main__'))

    @property
    def IconsDir(self):
        return os.path.join(self.resource_dir, 'icons')

    def LoadIconsInto(self, frame):
        icons = wx.IconBundle()

        if 'win32' in sys.platform:
            if os.path.exists('icons'):
                icons.AddIconFromFile('icons/fr0st.ico', wx.BITMAP_TYPE_ICO)
            else:
                icons.AddIconFromFile(os.path.join(self.IconsDir, 'fr0st.ico'), wx.BITMAP_TYPE_ICO)

        if os.path.exists(os.path.join(self.AppBaseDir, 'icons')):
            icons.AddIconFromFile(os.path.join(self.AppBaseDir, 'icons',  'fr0st.png'), wx.BITMAP_TYPE_PNG)
        else:
            icons.AddIconFromFile(os.path.join(self.IconsDir, 'fr0st.png'), wx.BITMAP_TYPE_PNG)

        frame.SetIcons(icons)


class MainWindow(wx.Frame):
    wildcard = "Flame file (*.flame)|*.flame|" \
               "All files (*.*)|*.*"
    scriptrunning = False


    @BindEvents
    def __init__(self,parent,id):
        self.title = "Fractal Fr0st"
        wx.Frame.__init__(self,parent,wx.ID_ANY, self.title)

        sys.excepthook = unhandled_exception_handler

        wx.GetApp().LoadIconsInto(self)

        self.CreateStatusBar()
        self.SetBackgroundColour(wx.NullColour)

        # Launch the render threads
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

        self.editor = EditorFrame(self)
        self.log = self.editor.log

        self.TreePanel = TreePanel(self)
        self.tree = self.TreePanel.tree

        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer3.Add(self.notebook,1,wx.EXPAND)

        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.image,0,wx.EXPAND)
        sizer2.Add(self.XformTabs.Selector,0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer2.Add(self.XformTabs,1,wx.EXPAND)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.TreePanel,0,wx.EXPAND)
        sizer.Add(sizer3,1,wx.EXPAND)
        sizer.Add(sizer2,0,wx.EXPAND)

        self.SetSizer(sizer)

        self.flame = self.MakeFlame()

        self.previewframe = PreviewFrame(self)

        # Calculate the correct minimum size dynamically.
        sizer.Fit(self)
        self.SetMinSize(self.GetSize())

        # Load frame positions from file
        for window, k in ((self, "Rect-Main"),
                          (self.editor, "Rect-Editor"),
                          (self.previewframe, "Rect-Preview")):
            if config[k]:
                rect, maximize = config[k]
                window.SetDimensions(*rect)
                window.Maximize(maximize)

        # Set up environment for scripts.
        sys.path.append(wx.GetApp().UserScriptsDir)
        self.PatchFr0stlib()

        flamepath = config["flamepath"]
        if os.path.exists(flamepath):
            self.OpenFlame(flamepath)
        else:
            self.MakeFlameFile(flamepath)

        self.tree.SelectItem(self.tree.GetItemByIndex((0,0)))

        self.Enable(ID.STOP, False, editor=True)
        self.Show(True)


#-----------------------------------------------------------------------------
# Event handlers

    @Bind(wx.EVT_MENU,id=ID.ABOUT)
    def OnAbout(self,e):
        wx.MessageDialog(self,"""%s

Copyright (c) 2008 - 2009 Vitor Bosshard

This program is free software.
View license.txt for more details.

Top Contributors:
Bobby R. Ward
Erik Reckase
John Miller

Built on top of:
flam3 - (c) 1992 - 2009 Scott Draves
flam4 - (c) 2009 Steven Broadhead""" % fr0stlib.VERSION,
                         "About Fractal Fr0st", wx.OK).ShowModal()

    @Bind(wx.EVT_MENU, id=wx.ID_PREFERENCES)
    def OnPreferences(self, evt):
        dlg = ConfigDialog(self)

        if dlg.ShowModal() == wx.ID_OK:
            dlg.CommitChanges()

        dlg.Destroy()

    @Bind(wx.EVT_CLOSE)
    @Bind(wx.EVT_MENU,id=ID.EXIT)
    def OnExit(self,e):
        # Check all widgets that might want to avoid closing the app.
        if self.renderdialog and self.renderdialog.OnExit() == wx.ID_NO:
            return
        self.OnStopScript()
        if self.editor.CheckForChanges() == wx.ID_CANCEL:
            return
        if self.tree.CheckForChanges() == wx.ID_CANCEL:
            return
        
        self.renderer.exitflag = True

        # Save size and pos of each window
        for window, k in ((self, "Rect-Main"),
                          (self.editor, "Rect-Editor"),
                          (self.previewframe, "Rect-Preview")):
            maximize = window.IsMaximized()
            # HACK: unmaximizing doesn't work properly in this context, so we
            # just use the previous config settings, even if it's not ideal.
##            window.Maximize(False)
            if maximize:
                (x,y,w,h), _ = config[k]
            else:
                x,y = window.GetPosition()
                w,h = window.GetSize()
            config[k] = (x,y,w,h), maximize
            
        self.Destroy()


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FNEW)
    def OnFlameNew(self, e):
        path = self.tree.GetFilePath()
        dlg = NewFileDialog(self, path=path)
        if dlg.ShowModal() == wx.ID_OK:
            newpath = dlg.GetPath()
            if os.path.exists(newpath):
                wx.MessageDialog(self, "%s already exists. "
                                 "Please choose a different file." % newpath,
                                 "Fr0st", wx.OK).ShowModal()
                self.OnFlameNew(e)
                return
            self.MakeFlameFile(newpath)
        

    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FNEW2)
    def OnFlameNew2(self, e=None, string=None):
        if string:
            flame = Flame(string)
        else:
            flame = self.MakeFlame()
        data = ItemData(flame.to_string())

        self.tree.GetChildItems((0,)).append((data,[]))
        self.tree.RefreshItems()

        # This is needed to avoid an indexerror when getting child.
        self.tree.Expand(self.tree.itemparent)

        child = self.tree.GetItemByIndex((0, -1))
        self.tree.SelectItem(child)
        self.tree.RenderThumbnail()
        self.SaveFlame()

        return child

    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=wx.ID_PASTE)
    def OnPaste(self, e):
        if not wx.TheClipboard.Open():
            return

        data = wx.TextDataObject()
        success = wx.TheClipboard.GetData(data)
        wx.TheClipboard.Close()

        if not success:
            return

        return self.OnFlameNew2(string=data.GetText())

    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=wx.ID_COPY)
    def OnCopy(self, e):
        s = self.flame.to_string()

        data = wx.TextDataObject()
        data.SetText(s)

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FOPEN)
    def OnFlameOpen(self,e):
        dDir,dFile = os.path.split(config["flamepath"])
        dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=dDir,
            defaultFile=dFile, wildcard=self.wildcard, style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            config["flamepath"] = dlg.GetPath()
            self.OpenFlame(config["flamepath"])
        dlg.Destroy()


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FSAVE)
    def OnFlameSave(self,e):
        config["flamepath"] = self.tree.GetFilePath()
        self.SaveFlame(config["flamepath"], confirm=False)


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.FSAVEAS)
    def OnFlameSaveAs(self,e):
        flame = self.flame
        path = self.tree.GetFilePath()
        dlg = SaveDialog(self, path=path, name=flame.name)
        if dlg.ShowModal() == wx.ID_OK:
            newpath = dlg.GetPath()
            flame.name = str(dlg.GetName())
            if path == newpath:
                self.OnFlameNew2(string=flame.to_string())
            else:
                if os.path.exists(newpath):
                    lst = fr0stlib.load_flame_strings(newpath)
                else:
                    lst = []
                lst.append(flame.to_string())
                save_flames(newpath, *lst)
        dlg.Destroy()


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.SOPEN)
    def OnScriptOpen(self,e):
        self.editor.OnScriptOpen(e)


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.RUN)
    def OnRunScript(self,e):
        self.BlockGUI(flag=True)
        self.Execute(self.editor.tc.GetText())


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.STOP)
    def OnStopScript(self,e=None):
        interruptall("Execute")


    @Bind((wx.EVT_MENU, wx.EVT_TOOL),id=ID.EDITOR)
    def OnEditorOpen(self,e):
        self.editor.Show(True)
        self.editor.Raise()
        self.editor.SetFocus() # In case it's already open in background


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

    def MakeFlame(self):
        flame = Flame()
        flame.add_xform()
        flame.gradient.random(**config["Gradient-Settings"])
        return flame


    def MakeFlameFile(self, path):
        path = os.path.abspath(path)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        save_flames(path, self.MakeFlame())
        self.OpenFlame(path)
        

    def OpenFlame(self, path):
        if self.tree.flamefiles:
            if path == self.tree.GetFilePath():
                # File is already open
                dlg = wx.MessageDialog(self, "%s is already open. Do you want to revert to its saved status?" % path,
                                       'Fr0st',wx.YES_NO|wx.CANCEL)
                if dlg.ShowModal() != wx.ID_YES:
                    return
            elif self.tree.CheckForChanges() == wx.ID_CANCEL:
                # User cancelled when prompted to save changes.
                return

            # Parent needs to be selected to avoid a possible indexerror when
            # reducing the size of the tree.
            self.tree.SelectItem(self.tree.itemparent)

        if os.path.exists(path):
            # scan the file to see if it's valid
            flamestrings = fr0stlib.load_flame_strings(path)
            if not flamestrings:
                wx.MessageDialog(self, "It seems %s is not a valid flame file."
                                 " Please choose a different flame." % path,
                                 'Fr0st',wx.OK).ShowModal()
                self.OnFlameOpen(None)
                return
        else:
            flamestrings = [self.MakeFlame()]

        # Add flames to the tree
        item = self.tree.SetFlames(path, *flamestrings)


    def SaveFlame(self, path=None, confirm=True):
        if path is None:
            path = self.tree.GetFilePath()

        lst = list(self.tree.GetDataGen())
    
        if self.tree.parentselected:
            for data, item in zip(lst, self.tree.GetItemChildren()):
                data.Reset()
                self.tree.SetItemText(item, data.name)
        else:
            data = self.tree.itemdata
            data.Reset()
            self.tree.SetItemText(self.tree.item, data.name)
                
        save_flames(path, *(data[0] for data in lst))
        # Make sure Undo and Redo get set correctly.
        self.SetFlame(self.flame, rezoom=False)


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
        if self.renderdialog:
            self.renderdialog.UpdateView()

        # Set Undo and redo buttons to the correct value:
        data = self.tree.itemdata
        self.Enable(ID.UNDOALL, data.undo)
        self.Enable(ID.UNDO, data.undo)
        self.Enable(ID.REDO, data.redo)
        self.Enable(ID.REDOALL, data.redo)


    def PatchFr0stlib(self):
        """Override some fr0stlib functions with equivalent GUI versions.
        References to the old functions must be explicitly kept for internal
        use ('from fr0stlib import ...')."""
        def new_save_flames(path, *flames):
            if not flames:
                raise ValueError("You must specify at least 1 flame to set.")

            if os.path.exists(path):
                dlg = wx.MessageDialog(self, "%s already exists. Do you want to overwrite?" % path,
                                       'Fr0st',wx.YES_NO)
                if dlg.ShowModal() != wx.ID_YES:
                    return

            lst = [s if type(s) is str else s.to_string() for s in flames]
            self.tree.SetFlames(path, *lst)
            save_flames(path, *lst)

        # These functions overwrite existing functions.
        fr0stlib.save_flames = InMain(new_save_flames)
        fr0stlib.load_flames = InMain(self.OpenFlame)
        fr0stlib.show_status = InMain(self.SetStatusText)

        # These are new, added functions.
        fr0stlib.get_flames = self.tree.GetFlames
        fr0stlib.get_file_path = self.tree.GetFilePath
        fr0stlib.preview = self.preview
        fr0stlib.large_preview = self.large_preview
        fr0stlib.dialog = self.editor.make_dialog
        

    def CreateNamespace(self):
        """Recreates the namespace each time the script is run to reassign
        the flame variable, etc."""
        namespace = dict(flame = self.flame,
                         update_flame = True,
                         # Make a copy of config, so it can't be modified.
                         config = deepcopy(config),
                         _self = self)
        exec("from fr0stlib import *; __name__='__main__'", namespace)
        return namespace


    @Threaded
    @Locked(blocking=True)
    def Execute(self,string):
        print time.strftime("\n---------- %H:%M:%S ----------")
        start = time.time()

        # split and join fixes linebreak issues between windows and linux
        lines = self.log._lines = string.splitlines()
        script = "\n".join(lines) +'\n'

        modules = dict(sys.modules)
        sys.path.insert(0, os.path.dirname(self.editor.scriptpath))
        
        oldflame = Flame(self.flame.to_string())
        namespace = self.CreateNamespace()

        try:
            # namespace is used as globals and locals, same as top level
            exec(script, namespace)
        except SystemExit:
            pass
        except ThreadInterrupt:
            print("\n\nScript Interrupted")
        finally:
            update = namespace["update_flame"]
            
            # Check if changes made to the flame by the script are legal.
            try:
                Flame(self.flame.to_string())
            except Exception as e:
                print "Error updating flame:"
                print e
                update = False
                
            # Remove any modules imported by the script, so they can be changed
            # without needing to restart fr0st. Also revert path.
            sys.modules.clear()
            sys.modules.update(modules)
            sys.path.pop(0)
                
            # Let the GUI know that the script has finished.
            self.EndOfScript(oldflame, update)

        # Keep this out of the finally clause!
        print "\nSCRIPT STATS:\n"\
              "Running time %.2f seconds\n" %(time.time()-start)


    @InMain
    def EndOfScript(self, oldflame, update):
        # Note that tempsave returns if scriptrunning == True, so it needs to
        # come after unblocking the GUI.
        self.BlockGUI(False)
        self.SetStatusText("")
        if update:
            self.TreePanel.TempSave()
        else:
            self.SetFlame(oldflame, rezoom=False)


    @CallableFrom('MainThread')
    def BlockGUI(self, flag=False):
        """Called before and after a script runs."""
        # TODO: prevent file opening, etc
        self.Enable(ID.RUN, not flag, editor=True)
        self.Enable(ID.STOP, flag, editor=True)
        self.editor.tc.SetEditable(not flag)
        self.scriptrunning = flag
        

    @CallableFrom('MainThread')
    def Enable(self, id, flag, editor=False):
        """Enables/Disables toolbar and menu items."""
        flag = bool(flag)
        self.tb.EnableTool(id, flag)
        self.menu.Enable(id, flag)
        if editor:
            self.editor.tb.EnableTool(id, flag)


    def preview(self):
        self.image.RenderPreview()
        self.OnPreview()
        time.sleep(.01) # Avoids spamming too many requests.


    def large_preview(self):
        if self.previewframe.IsShown():
            self.previewframe.RenderPreview()
        

    @InMain
    def OnPreview(self):
        # only update a select few of all the panels.
##        self.XformTabs.UpdateView()
##        self.notebook.UpdateView()
        self.canvas.ShowFlame(rezoom=False)
        self.grad.UpdateView()



class ImagePanel(PreviewBase):

    @BindEvents
    def __init__(self, parent):
        self.parent = parent
        # HACK: we change the class temorarily so the BindEvents decorator
        # catches the methods in the base class.
        self.__class__ = PreviewBase
        PreviewBase.__init__(self, parent)
        self.__class__ = ImagePanel

        # Double buffering is needed to prevent flickering.
        self.SetDoubleBuffered(True)
        
        self.SetSize((256, 220))
        self.bmp = wx.EmptyBitmap(400,300, 32)


    def GetPanelSize(self):
        return self.Size


    def RenderPreview(self, flame=None):
        """Renders a preview version of the flame and displays it in the gui.

        The renderer takes care of denying repeated requests so that at most
        one redundant preview is rendered."""
        flame = flame or self.parent.flame

        ratio = 200. / max(flame.size)
        size = [int(i * ratio) for i in flame.size]
        # We can't pass in the flame itself to the render request, since this
        # function is usually called on the same flame repeatedly, with changes
        # in rapid succession. To ensure correct rendering, the flame is
        # converted to string. Should be no big deal performance-wise.
        req = self.parent.renderer.PreviewRequest
        req(self.UpdateBitmap, flame.to_string(), size,
            **config["Preview-Settings"])


    def UpdateBitmap(self, bmp):
        """Callback function to process rendered preview images."""
        self.bmp = bmp
        self.Refresh()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, e):
        fw,fh = self.bmp.GetSize()
        pw,ph = self.GetPanelSize()
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, (pw-fw) / 2, (ph-fh) / 2, True)

