from __future__ import with_statement
import wx, sys, os, re, shutil, time, cPickle, itertools
from wx import PyDeadObjectError
from wx.lib.mixins import treemixin
from threading import Thread
import pickle as cPickle


from lib.fr0stlib import Flame
from lib.pyflam3 import Genome
from decorators import *
from itemdata import ItemData

class TreePanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.parent = parent
                       
        # Specify a size instead of using wx.DefaultSize
        self.tree = FlameTree(self, wx.NewId(), size=(180,500),
                               style=wx.TR_DEFAULT_STYLE
                                     #wx.TR_HAS_BUTTONS
                                     | wx.TR_EDIT_LABELS
                                     #| wx.TR_MULTIPLE
                                     | wx.TR_HIDE_ROOT
                                     )

##        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit, self.tree)
##        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.tree)
##        self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)


    def TempSave(self):
        """Updates the tree's undo list and saves a backup version from
        which the session can be restored."""
        
        # Update the child
        data = self.tree.itemdata
        string = self.parent.flame.to_string()
        data.append(string)
        self.tree.SetItemText(self.tree.item, data.name)
        self.tree.RenderThumbnail()
        self.parent.SetFlame(self.parent.flame,rezoom=False)

        data = self.tree.GetFlameData(self.tree.itemparent)
##        self.tree.SetItemText(self.tree.itemparent, '* ' + data.name)
        
        # Create the temp file.
        lst = [self.tree.GetFlameData(i)[1:]
               for i in self.tree.GetItemChildren()]
        with open(data[-1] + '.temp',"wb") as f:
            cPickle.dump(lst,f,cPickle.HIGHEST_PROTOCOL)


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


    def OnRightDown(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnRightClick: %s, %s, %s\n" %
                               (self.tree.GetItemText(item), type(item), item.__class__))
            self.tree.SelectItem(item)


    def OnRightUp(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:        
            self.log.WriteText("OnRightUp: %s (manually starting label edit)\n"
                               % self.tree.GetItemText(item))
            self.tree.EditLabel(item)  


    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self, event):       
        item = self.tree.item = event.GetItem()
        event.Skip()
        
        if self.tree._dragging:
            # Don't reselect flames when a drop is happening.
            return
        
        if item:
            string = self.tree.GetFlameData(item)[-1]
            if string.startswith('<flame'):
                self.parent.SetFlame(Flame(string=string))
            else:
                self.parent.EnableUndo(False)
                self.parent.EnableRedo(False)

        
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
        
        isz = (28,21)
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


    def AddFlamefile(self, path, flamestrings):
        lst = [(ItemData(s), []) for s in flamestrings]
        name = os.path.basename(path)
        self.flamefiles.append((ItemData(path, name=name),lst))

        self.RefreshItems()
        item = self.GetItemByIndex((-1,))
        self.Expand(item)

        for child, data in zip(self.GetItemChildren(item),
                               (i[0] for i in lst)):
            self.RenderThumbnail(child, data)
            # Set item to default until thumbnail is ready.    
            self.SetItemImage(child, 2)

        return item


    def RenderThumbnail(self, child=None, data=None):
        if child is None:
            child = self.item
            data = self.GetFlameData(child)
        data.imgindex = self.newimgindex()
        self.parent.parent.renderer.ThumbnailRequest(self.UpdateThumbnail,
                                     (child, data, self.isz),
                                     data[-1],self.isz,quality=25,estimator=3)
        

    def UpdateThumbnail(self, data, output_buffer):
        """Callback function to process rendered thumbnails."""
        child,data,(w,h) = data
        self.il.Add(wx.BitmapFromBuffer(w, h, output_buffer))
        self.SetItemImage(child, data.imgindex)


    def GetFlameData(self, item):
        """Gets the ItemData instance corresponding to item."""
        return self.GetItem(self.GetIndexOfItem(item))[0]


    def OnDrop(self, *args):
        """This method is used by the DragAndDrop mixin."""
        dropindex, dragindex = map(self.GetIndexOfItem, args)
        fromlist = self.GetChildren(dragindex[:1])
        tolist = self.GetChildren(dropindex[:1])

        # Makes the behaviour consistent even if flames move between files.
        HACK = fromlist != tolist

        fromindex = dragindex[1] if len(dragindex) > 1 else 0
        toindex = dropindex[1] + HACK if len(dropindex) > 1 else 0

        tolist.insert(toindex, fromlist.pop(fromindex))
        self.RefreshItems()

        if HACK:
            self.SelectItem(self.GetItemByIndex((dropindex[0],toindex)))

        self._dragging = False
        
        
    def OnGetItemText(self, indices):
        return self.GetItem(indices)[0].name

    def OnGetChildrenCount(self, indices):
        return len(self.GetChildren(indices))

    def OnGetItemImage(self, index, *args):
        return self.GetItem(index)[0].imgindex


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

    def _get_itemparent(self):
        if self.item:
            item = self.GetItemParent(self.item)
            if item == self.root:
                return self.item
            return item

    itemparent = property(_get_itemparent)


    def _get_itemdata(self):
        if self.item:
            return self.GetFlameData(self.item)

    itemdata = property(_get_itemdata)


    #-------------------------------------------------------------------------
    # These Methods override the DragAndDropMixin to produce desired behaviour


    def StartDragging(self):
        """When you start to drag an item, the panel will scroll up until the
        parent is visible, making it impossible to drop on lower items.
        Therefore, we don't bind EVT_MOTION to avoid calling OnDragging.
        Also, self._dragging is set to let OnSelChange know how to behave."""
##        self.GetMainWindow().Bind(wx.EVT_MOTION, self.OnDragging)
        self.Bind(wx.EVT_TREE_END_DRAG, self.OnEndDrag)
        self.SetCursorToDragging()
        self._dragging = True


    def IsValidDragItem(self, dragItem):
        """Make sure only flames can be dragged."""
        return dragItem and len(self.GetIndexOfItem(dragItem)) == 2


    def IsValidDropTarget(self, dropTarget):
        """The original method vetoes the dragItem's parent, but we want to
        allow that. Also, there's no need to check for children because our
        tree is flat."""
        return True 


    #-------------------------------------------------------------------------
    # These Methods override the VirtualTreeMixin for performance reasons.


    def RefreshItemImage(self, item, index, hasChildren):
        self.__refreshAttribute(item, index, 'ItemImage')


    def __refreshAttribute(self, item, index, attribute, *args):
        value = getattr(self, 'OnGet%s'%attribute)(index, *args)
        if getattr(self, 'Get%s'%attribute)(item, *args) != value:
            return getattr(self, 'Set%s'%attribute)(item, value, *args)
        else:
            return item


    def DoRefreshItem(self, item, index, hasChildren):
        item = self.RefreshItemType(item, index)
        self.RefreshItemText(item, index)
##        self.RefreshColumns(item, index)
##        self.RefreshItemFont(item, index)
##        self.RefreshTextColour(item, index)
##        self.RefreshBackgroundColour(item, index)
        self.RefreshItemImage(item, index, hasChildren)
##        self.RefreshCheckedState(item, index)
        return item
