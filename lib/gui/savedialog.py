import wx
from  wx.lib.filebrowsebutton import FileBrowseButton

class SaveDialog(wx.Dialog):
    def __init__(self, parent, path, name):
        wx.Dialog.__init__(self, parent, -1, "Save a copy of flame")

        ok = wx.Button(self, wx.ID_OK)
        cancel = wx.Button(self, wx.ID_CANCEL)
        ok.SetDefault()
        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(ok)
        btnsizer.AddButton(cancel)
        btnsizer.Realize()
        
        self.fbb = FileBrowseButton(self, -1, fileMask=parent.wildcard,
                                    labelText='File:  ', initialValue=path)
        self.nametc = wx.TextCtrl(self, -1)
        self.nametc.SetValue(name)
        self.nametc.SetMinSize((200,27))
        
        szr0 = wx.BoxSizer(wx.HORIZONTAL)
        szr0.Add(wx.StaticText(self, -1, "Name:"))
        szr0.Add(self.nametc)
                     
        szr = wx.BoxSizer(wx.VERTICAL)
        szr.AddMany(((self.fbb, 0, wx.EXPAND), szr0, btnsizer))
        
        self.SetMinSize((400,1))
        self.SetSizer(szr)
        szr.Fit(self)


    def GetPath(self):
        return self.fbb.GetValue()


    def GetName(self):
        return self.nametc.GetValue()
