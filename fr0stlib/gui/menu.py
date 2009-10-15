import wx
from functools import partial

from fr0stlib.gui.constants import ID


class Filemenu(wx.Menu):
    name = "&File"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.FNEW2, "&New Flame\tCtrl-N"," Create a new flame")        
##        self.Append(ID.FNEW, "&New File\tCtrl-Shift-N"," Create a new flame file")
        self.Append(ID.FOPEN, "&Open\tCtrl-O"," Open a flame file")
        self.Append(ID.FSAVE, "&Save\tCtrl-S"," Save a flame to a file")
        self.Append(ID.FSAVEAS, "&Save as\tCtrl-Shift-S"," Save a flame to a file")
        self.AppendSeparator()
        self.Append(ID.RENDER, "&Render\tCtrl-R"," Render a flame to an image")
        self.AppendSeparator()
        self.Append(ID.ABOUT, "&About"," Information about this program")
        self.AppendSeparator()
        self.Append(ID.EXIT,"E&xit\tCtrl-Q"," Terminate the program")

class Editmenu(wx.Menu):
    name = "&Edit"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.UNDO, "&Undo\tCtrl-Z", " Undo last change to the current flame.")
        self.Append(ID.UNDOALL, "U&ndo All\tCtrl-Shift-Z", " Undo all changes to the current flame.")
        self.Append(ID.REDO, "&Redo\tCtrl-Y", " Redo last change to the current flame.")
        self.Append(ID.REDOALL, "R&edo All\tCtrl-Shift-Y", "Redo all changes to the current flame.")

class Viewmenu(wx.Menu):
    name = "&View"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.PREVIEW, "&Preview\tCtrl-P", " Open the preview window.")

class Scriptmenu(wx.Menu):
    name = "&Script"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.RUN, "&Run\tF8"," Run currently open script")
        self.Append(ID.STOP, "&Stop\tF9"," Stop script execution")
        self.AppendSeparator()
        self.Append(ID.SOPEN, "&Open\tCtrl-Shift-O"," Open a script file")
        self.Append(ID.EDITOR, "&Editor\tCtrl-E"," Open the script editor")

class EditorFilemenu(wx.Menu):
    name = "&File"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.SNEW, "&New Script\tCtrl-N"," Create a new script")
        self.Append(ID.SOPEN, "&Open\tCtrl-O"," Open a script file")
        self.Append(ID.SSAVE, "&Save\tCtrl-S"," Save the current script")
        self.Append(ID.SSAVEAS, "&Save as\tCtrl-Shift-S"," Save the current script to a new file")
        self.AppendSeparator()
        self.Append(ID.RUN, "&Run\tF8"," Run currently open script")
        self.Append(ID.STOP, "&Stop\tF9"," Stop script execution")
        self.AppendSeparator()
        self.Append(ID.EXIT,"E&xit\tCtrl-Q"," Close the editor")        

class EditorEditmenu(wx.Menu):
    name = "&Edit"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.UNDO, "&Undo\tCtrl-Z", "")
        self.Append(ID.REDO, "&Redo\tCtrl-Shift-Z", "")
        

def Create(lst, parent):
    menu = wx.MenuBar()
    map(menu.Append,*zip(*((menu(), menu.name) for menu in lst)))
    parent.SetMenuBar(menu)
    parent.menu = menu

CreateMenu = partial(Create, (Filemenu, Editmenu, Viewmenu, Scriptmenu))
CreateEditorMenu = partial(Create, (EditorFilemenu, EditorEditmenu))
