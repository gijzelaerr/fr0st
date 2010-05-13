import wx, os

from fr0stlib.gui.config import config
from fr0stlib.gui.utils import ErrorMessage


id_counter = wx.ID_FILE1

class MyFileHistory(wx.FileHistory):
    def __init__(self, parent, configname, callback, n=4):
        self.parent = parent
        self.configname = configname
        self.callback = callback
        self.n = n

        global id_counter
        self.id = id_counter
        id_counter += n
        
        wx.FileHistory.__init__(self, n, idBase=self.id)
        map(self.AddFileToHistory, reversed(config[configname]))
        self.BindMenu(parent)


    def BindMenu(self, parent, pos=0):
        menu = parent.menu.GetMenu(pos)
        self.UseMenu(menu)
        parent.Bind(wx.EVT_MENU_RANGE, self.OnHistory,
                    id=self.id, id2=self.id + self.n)
        self.AddFilesToThisMenu(menu)
        

    def SaveToConfig(self):
        config[self.configname] = tuple(self.GetHistoryFile(i)
                                        for i in range(self.GetCount()))


    def OnHistory(self, e):
        index = e.GetId() - self.id
        if not index:
            return
        path = self.GetHistoryFile(index)
        if not os.path.exists(path):
            ErrorMessage(self.parent, "Could not find %s." % path)
            self.RemoveFileFromHistory(index)
            return
        self.callback(path)
