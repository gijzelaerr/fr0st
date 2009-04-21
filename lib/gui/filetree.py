from __future__ import with_statement
import wx, sys, os, re, shutil, time, cPickle, itertools
from wx import PyDeadObjectError
from threading import Thread
import pickle as cPickle


from lib.fr0stlib import Flame
from lib.pyflam3 import Genome
from lib import functions
from decorators import *
from _events import EVT_IMAGE_READY
from itemdata import ItemData

class TreePanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.parent = parent
        self.item = None
                       
        # Specify a size instead of using wx.DefaultSize
        self.tree = wx.TreeCtrl(self, wx.NewId(), wx.DefaultPosition, (180,500),
                               wx.TR_DEFAULT_STYLE
                               #wx.TR_HAS_BUTTONS
                               | wx.TR_EDIT_LABELS
                               #| wx.TR_MULTIPLE
                               | wx.TR_HIDE_ROOT
                               )

        # Change font size so that it fits nicely with images
        font = self.GetFont()
        font.SetPointSize(9)
        self.tree.SetFont(font)

        
        isz = (28,21)
        il = wx.ImageList(*isz)
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

        self.tree.SetImageList(il)
        self.il = il
        self.isz = isz
        self.imgcount = 2

        self.root = self.tree.AddRoot("The Root Item")

##        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit, self.tree)
##        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.tree)
##        self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)


    def RenderThumbnails(self, item):
        for child in self.iterchildren(item):
            self.RenderThumbnail(child)
            # Set item to default until thumbnail is ready.    
            self.tree.SetItemImage(child, 2)           


    def RenderThumbnail(self,child=None):
        if child is None:
            child = self.item
        data = self.tree.GetPyData(child)
        self.imgcount += 1
        self.parent.renderer.Request(self.UpdateThumbnail,
                                     (child,self.imgcount,self.isz),
                                     data[-1],self.isz,quality=25,estimator=3)

            
    def UpdateThumbnail(self, data, output_buffer):
        """Callback function to process rendered thumbnails."""
        child,num,(w,h) = data
        self.il.Add(wx.BitmapFromBuffer(w, h, output_buffer))
        self.tree.SetItemImage(child,num)


    def iterchildren(self,item=None):
        if item is None:
            item = self.itemparent
        child,cookie = self.tree.GetFirstChild(item)
        while child.IsOk():
            yield child
            child,cookie = self.tree.GetNextChild(item,cookie)


    def NewItem(self, path):
        name = os.path.basename(path)
        item = self.tree.AppendItem(self.root, name)
        self.tree.SetPyData(item, ItemData(name, path))
        self.tree.SetItemImage(item, 0, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(item, 1, wx.TreeItemIcon_Expanded)
        return item


    def TempSave(self):
        """Updates the tree's undo list and saves a backup version from
        which the session can be restored."""
        
        # Update the child
        data = self.itemdata
        string = self.parent.flame.to_string()
        data.append(string)
        self.tree.SetItemText(self.item, data.name)
        self.RenderThumbnail()
        self.parent.SetFlame(self.parent.flame,rezoom=False)

        data = self.tree.GetPyData(self.itemparent)
##        self.tree.SetItemText(self.itemparent, '* ' + data.name)
        
        # Create the temp file.
        lst = [self.tree.GetPyData(i)[1:] for i in self.iterchildren()]
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
                self.item = self.parent.OpenFlame(path)
            else:
                self.item = self.parent.OnFlameNew(None)
                
            # This is an ad-hoc izip_longest (2.6 feature!)
            itr = itertools.chain(self.iterchildren(), itertools.repeat(None))
            for child,lst in zip(itr, undolist):
                if child is None:
                    child = self.parent.OnFlameNew2(None)
                data = self.tree.GetPyData(child)
                data.extend(lst)
                self.tree.SetItemText(child,data.name)
                self.RenderThumbnail(child)
                self.tree.SelectItem(child)


##    @Bind(wx.EVT_RIGHT_DOWN) # this bind doesn't work
    def OnRightDown(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnRightClick: %s, %s, %s\n" %
                               (self.tree.GetItemText(item), type(item), item.__class__))
            self.tree.SelectItem(item)

##    @Bind(wx.EVT_RIGHT_UP) # this bind doesn't work
    def OnRightUp(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:        
            self.log.WriteText("OnRightUp: %s (manually starting label edit)\n"
                               % self.tree.GetItemText(item))
            self.tree.EditLabel(item)  


    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self, event):
        self.item = event.GetItem()
        if self.item:
            string = self.tree.GetPyData(self.item)[-1]
            if string.startswith('<flame'):
##                self.parent.canvas.ActiveXform = None
                self.parent.SetFlame(Flame(string=string))
            else:
                self.parent.EnableUndo(False)
                self.parent.EnableRedo(False)
        event.Skip()

        
    @Bind(wx.EVT_TREE_END_LABEL_EDIT)
    def OnEndEdit(self, e):
        item = e.GetItem()
        data = self.tree.GetPyData(item)
        newname = str(e.GetLabel())
        # Make sure edits don't change the name to an empty string
        if newname:
            data.name = newname
        self.tree.SetItemText(item, data.name)
        e.Veto()


    def _get_itemparent(self):
        if self.item:
            item = self.tree.GetItemParent(self.item)
            if item == self.root:
                return self.item
            return item

    itemparent = property(_get_itemparent)


    def _get_itemdata(self):
        if self.item:
            return self.tree.GetPyData(self.item)

    itemdata = property(_get_itemdata)

