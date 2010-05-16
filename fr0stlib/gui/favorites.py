import wx, os
from wx import gizmos
from functools import partial

from fr0stlib.decorators import *
from fr0stlib.gui.config import config
from fr0stlib.gui.utils import ErrorMessage
from fr0stlib.gui.constants import ID, NewIdRange


class FavoritesMenu(wx.Menu):
    name = "&Favorites"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.MANAGE, "&Manage...", "Manage your favorites.")
        self.AppendSeparator()

        

class FavoritesHandler(object):
    def __init__(self, parent):
        self.id = NewIdRange(12)
        self.menus = menu1, menu2 = FavoritesMenu(), FavoritesMenu()
        
        parent.menu.Append(menu2, menu2.name)
        parent.Bind(wx.EVT_MENU_RANGE, partial(self.OnFavorite, parent),
                    id=self.id, id2=self.id + 12)
        parent.Bind(wx.EVT_MENU, partial(self.OnManage, parent),
                    id=ID.MANAGE)
        
        main = parent.parent
        main.menu.GetMenu(3).InsertMenu(2, -1, menu1.name, menu1)
        main.Bind(wx.EVT_MENU_RANGE, partial(self.OnFavorite, main),
                  id=self.id, id2=self.id + 12)
        main.Bind(wx.EVT_MENU, partial(self.OnManage, main),
                  id=ID.MANAGE) 

        self.max = 0
        self.Load(config["Favorite-Scripts"])
        self.wildcard = parent.wildcard
        self.callback = main.Execute


    def Load(self, lst):
        for menu in self.menus:
            for i in range(self.max):
                menu.Delete(self.id + i)
            for i, path in enumerate(lst):
                menu.Append(self.id + i, "&%s\tCtrl-F%s"
                            %(os.path.basename(str(path)), i+1))
        self.max = i + 1
        self.lst = lst


    def SaveToConfig(self):
        config["Favorite-Scripts"] = self.lst
 
        
    def OnFavorite(self, parent, e):
        index = e.GetId() - self.id
        path = self.lst[index]
        if path is None:
            return
        if not os.path.exists(path):
            ErrorMessage(parent, "Could not find %s." % path)
        self.callback(open(path).read())


    def OnManage(self, parent, e):
        dlg = ManageDialog(self, parent, self.lst)
        if dlg.ShowModal() == wx.ID_OK:
            self.Load(dlg.lst)
        


class ManageDialog(wx.Dialog):
    @BindEvents
    def __init__(self, parent, frame, lst):
        wx.Dialog.__init__(self, frame, -1, title="Manage Favorites")
        self.parent = parent
        self.lst = lst[:]
        
        self.tree = gizmos.TreeListCtrl(self, -1,
                                        style =
                                          wx.TR_DEFAULT_STYLE
                                        | wx.TR_NO_LINES
                                        | wx.TR_HIDE_ROOT
                                        | wx.TR_FULL_ROW_HIGHLIGHT
                                   )

        self.tree.AddColumn("Script")
        self.tree.AddColumn("Shortcut")
        self.tree.SetColumnWidth(0, 300)
        self.tree.SetColumnWidth(1, 90)
        self.tree.SetMinSize((400,300))

        self.UpdateSelector(0)
        buttons = [wx.Button(self, i, name, style=wx.BU_EXACTFIT)
                   for (i, name) in ((ID.EDIT, 'Choose Script...'),
                                     (ID.REMOVE, 'Remove'),
                                     (ID.MOVEUP, 'Move Up'),
                                     (ID.MOVEDOWN, 'Move Down'))]
        btn_szr = wx.BoxSizer(wx.HORIZONTAL)
        btn_szr.AddMany(buttons)

        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(btn_szr)
        szr.Add(self.tree, 0, wx.EXPAND)

        btnsizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        if btnsizer:
            szr.Add(btnsizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        self.SetSizerAndFit(szr)
        
        
    def UpdateSelector(self, selection=None):
        if selection is None:
            selection = self.tree.GetPyData(self.tree.Selection)
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot("The Root Item")
        for i, string in enumerate(self.lst):
            item = self.tree.AppendItem(root, string)
            self.tree.SetItemText(item, os.path.basename(string), 0)
            self.tree.SetItemText(item, "Ctrl-F%s" % (i+1), 1)
            self.tree.SetPyData(item, i)
            if i == selection:
                self.tree.SelectItem(item)

    
    def wrapper(f):
        def inner(self, e):
            selection = self.tree.GetPyData(self.tree.GetSelection())
            f(self, selection)
            self.UpdateSelector()
        return inner
    

    @Bind(wx.EVT_BUTTON, id=ID.EDIT)
    @wrapper
    def OnEdit(self, selection):
        path = self.lst[selection]
        if path == "None":
            dDir = os.path.join(wx.GetApp().UserScriptsDir)
            dFile = ""
        else:
            dDir,dFile = os.path.split(path)
        dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=dDir,
            defaultFile=dFile, wildcard=self.parent.wildcard, style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.lst[selection] = dlg.GetPath()
        dlg.Destroy()
        self.UpdateSelector()


    @Bind(wx.EVT_BUTTON, id=ID.REMOVE)
    @wrapper
    def OnRemove(self, selection):
        self.lst[selection] = "None"
        self.UpdateSelector()


    @Bind(wx.EVT_BUTTON, id=ID.MOVEUP)
    @wrapper
    def OnMoveUp(self, selection):
        newsel = max(0, selection - 1)
        self.lst.insert(newsel, self.lst.pop(selection))
        self.UpdateSelector(newsel)


    @Bind(wx.EVT_BUTTON, id=ID.MOVEDOWN)
    @wrapper
    def OnMoveDown(self, selection):
        newsel = min(11, selection + 1)
        self.lst.insert(newsel, self.lst.pop(selection))
        self.UpdateSelector(newsel)
   
