import wx, os
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
        
        self.lb = wx.ListBox(self, -1, size=(400,300))
        self.UpdateSelector(0)
        buttons = [wx.Button(self, i, name, style=wx.BU_EXACTFIT)
                   for (i, name) in ((ID.EDIT, 'Choose File...'),
                                     (ID.REMOVE, 'Remove'),
                                     (ID.MOVEUP, 'Move Up'),
                                     (ID.MOVEDOWN, 'Move Down'))]
        btn_szr = wx.BoxSizer(wx.HORIZONTAL)
        btn_szr.AddMany(buttons)

        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(btn_szr)
        szr.Add(self.lb, 0, wx.EXPAND)

        btnsizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        if btnsizer:
            szr.Add(btnsizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
            
        self.SetSizerAndFit(szr)
        
        
    def UpdateSelector(self, selection=None):
        if selection is None:
            selection = self.lb.GetSelection()
        self.lb.Clear()
        self.lb.AppendItems(["Ctrl-F%s\t%s"
                             %(i+1, os.path.basename(str(item)))
                             for i, item in enumerate(self.lst)])
        self.lb.SetSelection(selection)

    
    def wrapper(f):
        def inner(self, e):
            selection = self.lb.GetSelection()
            if selection == -1:
                return
            f(self, selection)
            self.UpdateSelector()
        return inner
    

    @Bind(wx.EVT_BUTTON, id=ID.EDIT)
    @wrapper
    def OnEdit(self, selection):
        dDir,dFile = os.path.split(wx.GetApp().UserScriptsDir)
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
        self.lst[selection] = None
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
   
