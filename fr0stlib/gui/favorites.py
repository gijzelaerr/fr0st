
import wx, os
from fr0stlib.gui.config import config
from fr0stlib.gui.utils import ErrorMessage
from fr0stlib.gui.constants import NewIdRange


class FavoritesMenu(wx.Menu):
    name = "&Favorites"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.MANAGE, "&Manage...", "Manage your favorites.")
        self.AppendSeparator()


# TODO: implement manage favorites modal dialog
# TODO: put default favorites tuple into config.


class FavoritesHandler(object):
    def __init__(self, parent, menuindex=0, pos=2):
        self.parent = parent
        menu = parent.menu.GetMenu(menuindex)
        self.menu = FavoritesMenu()
        
        menu.InsertMenu(pos, -1, favorites.name, favorites)

        parent.Bind(wx.EVT_MENU_RANGE, self.OnFavorite,
                    id=self.id, id2=self.id + 12)   


    def Load(self, lst):
        # TODO: clear list before repopulating

        for i, path in enumerate(lst):
            self.menu.Append(self.id + i, "&{0} {1} Ctrl-F{0}".format(
                i+1, os.path.basename(path))) 
        self.lst = lst
        
        
    def OnFavorite(self, e):
        parent = self.parent
        index = e.GetId() - self.id
        path = self.lst[index]
        if not os.path.exists(path):
            ErrorMessage(parent, "Could not find %s." % path)
        parent.SetStatusText("Running Script: %s" %os.path.basename(path))
        parent.Execute(open(path).read())

