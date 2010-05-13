import wx, os

from fr0stlib.gui.config import config
from fr0stlib.gui.utils import ErrorMessage


class MyFileHistory(wx.FileHistory):
    def __init__(self, parent, configname, callback, n=4):
        wx.FileHistory.__init__(self, n)
        map(self.AddFileToHistory, reversed(config[configname]))
        self.UseMenu(parent.menu.GetMenu(0))
        self.AddFilesToMenu()
        self.configname = configname
        self.callback = callback
        parent.Bind(wx.EVT_MENU_RANGE, self.OnHistory,
                    id=wx.ID_FILE1, id2=wx.ID_FILE9)


    def SaveToConfig(self):
        config[self.configname] = tuple(self.GetHistoryFile(i)
                                        for i in range(self.GetCount()))


    def OnHistory(self, e):
        index = e.GetId() - wx.ID_FILE1
        path = self.GetHistoryFile(index)
        if not os.path.exists(path):
            ErrorMessage(self, "Could not find %s." % path)
            self.RemoveFileFromHistory(index)
            return
        self.callback(path)
