import wx
from constants import ID


class Filemenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.FNEW2, "&New Flame\tCtrl-N"," Create a new flame")        
        self.Append(ID.FNEW, "&New File\tCtrl-Shift-N"," Create a new flame file")
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
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.UNDO, "&Undo\tCtrl-Z"," Undo last change to the selected flame.")
        self.Append(ID.REDO, "&Redo\tCtrl-Shift-Z"," Redo last change to the selected flame.")

class Scriptmenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.RUN, "&Run\tF8"," Run currently open script")
        self.Append(ID.STOP, "&Stop\tF9"," Stop script execution")
        self.Append(ID.SOPEN, "&Open\tCtrl-Shift-O"," Open a script file")
        self.Append(ID.EDITOR, "&Editor\tCtrl-E"," Open the script editor")
        self.AppendSeparator()


def CreateMenu(parent):
    menu = wx.MenuBar()
    lst = [(Filemenu(),   "&File"),
           (Editmenu(),   "&Edit"),
           (Scriptmenu(), "&Script")]
    
    map(menu.Append,*zip(*lst))
    parent.SetMenuBar(menu)
    parent.menu = menu

