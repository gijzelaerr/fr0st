import wx
from constants import ID


class Filemenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.FOPEN, "&Open"," Open a flame file")
        self.Append(ID.FSAVE, "&Save"," Save a flame to a file")
        self.AppendSeparator()
        self.Append(ID.ABOUT, "&About"," Information about this program")
        self.AppendSeparator()
        self.Append(ID.EXIT,"E&xit"," Terminate the program")


class Scriptmenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.SOPEN, "&Open"," Open a script file")
        self.Append(ID.SSAVE, "&Save"," Save a script file")
        self.AppendSeparator()


def CreateMenu(parent):
    menu = wx.MenuBar()
    lst = [(Filemenu(),   "&File"),
           (Scriptmenu(), "&Script")]
    
    map(menu.Append,*zip(*lst))
    parent.SetMenuBar(menu)

