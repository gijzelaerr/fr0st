from __future__ import with_statement
import wx, sys, os, shutil, time, cPickle, itertools, pickle as cPickle
from functools import partial
from wx.lib.mixins import treemixin

from fr0stlib.gui.constants import ID
from fr0stlib import Flame
from fr0stlib.decorators import *
import fr0stlib
from fr0stlib.gui.itemdata import ItemData


class TreePanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.parent = parent

        # Specify a size instead of using wx.DefaultSize
        self.tree = FlameTree(self, wx.NewId(), size=(180,520),
                               style=wx.TR_DEFAULT_STYLE
                                     #wx.TR_HAS_BUTTONS
                                     | wx.TR_EDIT_LABELS
                                     #| wx.TR_MULTIPLE
                                     | wx.TR_HIDE_ROOT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()


    def TempSave(self, force=False):
        """Updates the tree's undo list and saves a backup version from
        which the session can be restored."""
        # HACK: this prevents loads of useless tempsaves when running a script.
        # the GUI can still be manipulated. This also prevents some weird
        # segfaults.
        if self.parent.scriptrunning:
            return

        data = self.tree.itemdata

        string = self.parent.flame.to_string()
        # Check if flame has changed. to_string is needed to detect identical
        # flames saved in different apps. This comparison takes about 5ms.
        if not force and Flame(data[-1]).to_string() == string:
            return

        # Update the child
        data.append(string)
        self.tree.SetItemText(self.tree.item, data.name)
        self.tree.RenderThumbnail()
        self.parent.SetFlame(self.parent.flame,rezoom=False)

        data = self.tree.GetFlameData(self.tree.itemparent)
##        self.tree.SetItemText(self.tree.itemparent, '* ' + data.name)

        # Create the temp file.
##        lst = [self.tree.GetFlameData(i)[1:]
##               for i in self.tree.GetItemChildren()]
##        with open(data[-1] + '.temp',"wb") as f:
##            cPickle.dump(lst,f,cPickle.HIGHEST_PROTOCOL)


    def RecoverSession(self,paths):
        """Restores a working session based on the temp files left by a
        previous run of the program. Creates backups of the temp files in case
        manual recovery becomes necessary."""
        # Get this data now to be used later.
        temppaths = [i+'.temp' for i in paths]
        undolists = []
        for path in temppaths:
            if os.path.exists(path):
                lst = cPickle.load(open(path,"rb"))
            else:
                lst = []
            undolists.append(lst)

        # Create the backup files.
        targetdir = os.path.join(sys.path[0], 'recovery',
                                 time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(targetdir)
        shutil.move('paths.temp',os.path.join(targetdir,'paths.temp'))
        for path in filter(os.path.exists,temppaths):
            newpath = os.path.join(targetdir,os.path.basename(path))
            if os.path.exists(newpath):
                # Make sure different files with the same basename don't clash.
                number = 2
                while os.path.exists(newpath):
                    head, ext = os.path.splitext(newpath)
                    newpath = '%s (%s)%s' %(head,number,ext)
                    number += 1
            shutil.copy(path,newpath)

        # Finally, recover the actual session
        for path,undolist in zip(paths,undolists):
            if os.path.exists(path):
                self.tree.item = self.parent.OpenFlame(path)
            else:
                self.tree.item = self.parent.OnFlameNew(None)

            # This is an ad-hoc izip_longest (2.6 feature!)
            itr = itertools.chain(self.tree.GetItemChildren(),
                                  itertools.repeat(None))
            for child,lst in zip(itr, undolist):
                if child is None:
                    child = self.parent.OnFlameNew2(None)
                data = self.tree.GetFlameData(child)
                data.extend(lst)
                self.tree.SetItemText(child,data.name)
                self.tree.RenderThumbnail(child)


    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self, event):
        item = event.GetItem()
        event.Skip()

        if self.tree._dragging:
            # Don't reselect flames when a drop is happening.
            return

        if item and len(self.tree.GetIndexOfItem(item)) == 2:
            # Item is a flame
            self.tree.item = item
            self.tree.parentselected = False
            string = self.tree.GetFlameData(item)[-1]
            self.parent.SetFlame(Flame(string=string))
        else:
            # Item is a flamefile
            self.tree.parentselected = True
            self.parent.Enable(ID.UNDO, False)
            self.parent.Enable(ID.REDO, False)


    @Bind(wx.EVT_TREE_END_LABEL_EDIT)
    def OnEndEdit(self, e):
        item = e.GetItem()
        data = self.tree.GetFlameData(item)
        newname = str(e.GetLabel())
        # Make sure edits don't change the name to an empty string
        if newname:
            data.name = newname
        self.tree.SetItemText(item, data.name)
        e.Veto()


    @Bind(wx.EVT_CONTEXT_MENU)
    def OnContext(self, e):
        menu = wx.Menu()
        menu.Append(ID.RENAME, "Rename")
        menu.Append(ID.DELETE, "Delete")
        self.PopupMenu(menu)
        menu.Destroy()


    @Bind(wx.EVT_MENU, id=ID.RENAME)
    def OnRename(self, e):
        self.tree.EditLabel(self.tree.item)


    @Bind(wx.EVT_MENU, id=ID.DELETE)
    def OnDelete(self, e):
        index = self.tree.GetIndexOfItem(self.tree.item)[-1]
        children = self.tree.GetChildren((0,))
        children.pop(index)
        if not children:
            # Make sure the flamefile is never empty.
            self.parent.OnFlameNew2()
        self.tree.RefreshItems()
        if index >= len(children):
            index = len(children) - 1
        self.tree.SelectItem(self.tree.itemparent)
        self.tree.SelectItem(self.tree.GetItemByIndex((0,index)))
        self.parent.SaveFlame()

    @Bind(wx.EVT_TREE_ITEM_COLLAPSING)
    def OnTreeItemCollapsing(self, evt):
        item = evt.GetItem()
        parent = self.tree.GetItemParent(item)

        if parent == self.tree.root:
            evt.Veto()
            



        


class FlameTree(treemixin.DragAndDrop, treemixin.VirtualTree, wx.TreeCtrl):
    newimgindex = itertools.count(3).next

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        super(FlameTree, self).__init__(parent, *args, **kwargs)

        # Change font size so it fits nicely with images
        font = self.GetFont()
        font.SetPointSize(9)
        self.SetFont(font)

        self.Indent = 8 # default is 15
        self.Spacing = 12 # default is 18

        isz = (23,23)
        il = wx.ImageList(*isz)
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

        self.SetImageList(il)
        self.il = il
        self.isz = isz

        self.root = self.AddRoot("The Root Item")
        self.item = None
        self.flamefiles = []
        self._dragging = False


    def SetFlames(self, path, *flamestrings):
        lst = [(ItemData(s), []) for s in flamestrings]
        name = os.path.basename(path)
        self.flamefiles = [(ItemData(path, name=name),lst),]

        self.RefreshItems()
        parent = self.itemparent

        self.Expand(parent)

        for child, data in zip(self.GetItemChildren(parent),
                               (i[0] for i in lst)):
            self.RenderThumbnail(child, data)
            # Set item to default until thumbnail is ready.
            self.SetItemImage(child, 2)

        self.SelectItem(parent)
        self.SelectItem(self.GetItemByIndex((0,0)))

        return parent


    def RenderThumbnail(self, child=None, data=None):
        if child is None:
            child = self.item
            data = self.GetFlameData(child)
        data.imgindex = self.newimgindex()
        # This is the only place where a request is made directly with a
        # string. The _flam3_render function checks for this special case.
        callback = partial(self.UpdateThumbnail, child=child, data=data)
        self.parent.parent.renderer.ThumbnailRequest(callback,data[-1],
                                            self.isz,quality=10,estimator=1,
                                                     filter_radius=0)


    def UpdateThumbnail(self, bmp, child, data):
        """Callback function to process rendered thumbnails."""
        self.il.Add(bmp)
        self.SetItemImage(child, data.imgindex)


    def GetFlameData(self, item):
        """Gets the ItemData instance corresponding to item."""
        return self.GetItem(self.GetIndexOfItem(item))[0]


    def GetFilePath(self):
        return self.GetItem((0,))[0][-1]


    def OnDrop(self, *args):
        """This method is used by the DragAndDrop mixin."""
        dropindex, dragindex = map(self.GetIndexOfItem, args)
        if not dropindex:
            return

        lst = self.GetChildren((0,))

        fromindex = dragindex[1] if len(dragindex) > 1 else 0
        toindex = dropindex[1] +1 if len(dropindex) > 1 else 0

        lst.insert(toindex, lst.pop(fromindex))

        self.RefreshItems()
        index = (0, min(toindex, len(lst)-1))
        self.SelectItem(self.GetItemByIndex(index))

        self._dragging = False
        
        fr0stlib.save_flames(self.GetFilePath(),
                             *(data[0] for data in self.GetDataList()))


    def GetItem(self, indices):
        data, children = " ", self.flamefiles
        for index in indices:
            data, children = children[index]
        return data, children


    def GetChildren(self, indices):
        return self.GetItem(indices)[1]


    def GetItemChildren(self, item=None):
        if item is None:
            item = self.itemparent
        return treemixin.VirtualTree.GetItemChildren(self, item)


    @property
    def itemparent(self):
        return self.GetItemByIndex((-1,))


    @property
    def itemdata(self):
        if self.item:
            return self.GetFlameData(self.item)


    def GetDataList(self):
        return [i for i,_ in self.GetChildren((0,))]


    def GetFlames(self, type=Flame):
        """Returns all flames in the currently selected file. Type can be Flame
        (default) or str. Meant to be called from a script."""
        return [type(i[-1]) for i in self.GetDataList()]


    #-------------------------------------------------------------------------
    # These Methods are used by the VirtualTreeMixin.

    def OnGetItemText(self, indices):
        return self.GetItem(indices)[0].name

    def OnGetChildrenCount(self, indices):
        return len(self.GetChildren(indices))

    def OnGetItemImage(self, indices, *args):
        if len(indices) == 1:
            # It's a flamefile
            return 0
        return self.GetItem(indices)[0].imgindex


    #-------------------------------------------------------------------------
    # These Methods override the DragAndDropMixin to produce desired behaviour

    def StartDragging(self):
        """When you start to drag an item, the panel will scroll up until the
        parent is visible, making it impossible to drop on lower items.
        Therefore, we don't bind EVT_MOTION to avoid calling OnDragging.
        Also, self._dragging is set to let OnSelChanged know how to behave."""
##        self.GetMainWindow().Bind(wx.EVT_MOTION, self.OnDragging)
        self.Bind(wx.EVT_TREE_END_DRAG, self.OnEndDrag)
        self.SetCursorToDragging()
        self._dragging = True


    def IsValidDragItem(self, dragItem):
        """Make sure only flames can be dragged."""
        return dragItem and dragItem != self.itemparent


    def IsValidDropTarget(self, dropTarget):
        """The original method vetoes the dragItem's parent, but we want to
        allow that. Also, there's no need to check for children because our
        tree is flat."""
        return True
