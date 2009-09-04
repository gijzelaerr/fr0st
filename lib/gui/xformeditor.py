import wx, os, functools, itertools
from wx import gizmos
from collections import defaultdict
from functools import partial

from lib.decorators import Bind,BindEvents
from lib.fr0stlib import polar, rect
from lib import pyflam3
from lib.gui.config import config
from lib.gui.utils import LoadIcon, MultiSliderMixin, NumberTextCtrl


class XformTabs(wx.Notebook):

    def __init__(self, parent):
        self.parent = parent
        wx.Notebook.__init__(self, parent, -1, size=(262,100), style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )

        self.Xform = XformPanel(self)
        self.AddPage(self.Xform, "Xform")

        self.Vars = VarPanel(self)
        self.AddPage(self.Vars, "Vars")

        self.Color = ColorPanel(self)
        self.AddPage(self.Color, "Color")

        self.Chaos = ChaosPanel(self)
        self.AddPage(self.Chaos, "Chaos")

        self.Selector = wx.Choice(self.parent, -1)
        self.Selector.Bind(wx.EVT_CHOICE, self.OnChoice)


    def UpdateView(self):
        for i in self.Xform, self.Vars, self.Color, self.Chaos:
            i.UpdateView()
            
        choices = map(repr, self.parent.flame.xform)
        final = self.parent.flame.final
        if final:
            choices.append(repr(final))
        self.Selector.Items = choices
        index = self.parent.ActiveXform.index
        self.Selector.Selection = len(choices)-1 if index is None else index


    def OnChoice(self, e):
        index = e.GetInt()
        xforms = self.parent.flame.xform
        if index >= len(xforms):
            self.parent.ActiveXform = self.parent.flame.final
        else:
            self.parent.ActiveXform = xforms[index]

        self.parent.canvas.ShowFlame(rezoom=False)
        self.UpdateView()



class XformPanel(wx.Panel):
    _rotate = 15
    _translate = 0.1
    _scale = 1.25

    choices = {"rotate": map(str, (5, 15, 30, 45, 60, 90, 120, 180)),
               "translate": map(str,(1.0, 0.5, 0.25, 0.1, 0.05, 0.025, 0.001)),
               "scale": map(str, (1.1, 1.25, 1.5, 1.75, 2.0))}

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        # The view tells us what attributes need to be displayed
        self._view = [False, "triangle"]
        self.parent = parent.parent

        # Add the number fields
        map(lambda x: setattr(self,x,NumberTextCtrl(self)), "adbecf")
        btn = (wx.Button(self,-1,i,name=i,style=wx.BU_EXACTFIT) for i in "xyo")

        fgs = wx.FlexGridSizer(3,3,1,1)
        itr = (getattr(self, i) for i in "adbecf")
        fgs.AddMany(itertools.chain(*zip(btn, itr, itr)))


        # Add the view buttons
        r1 = wx.RadioButton(self, -1, "triangle", style = wx.RB_GROUP )
        r2 = wx.RadioButton(self, -1, "xform" )
        r3 = wx.RadioButton(self, -1, "polar" )
        self.postflag = wx.CheckBox(self,-1,"post  ")
        radiosizer = wx.BoxSizer(wx.VERTICAL)
        radiosizer.AddMany((r1,r2,r3,self.postflag))

        # Put the view buttons to the right of the number fields
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddMany((fgs, radiosizer))

        # Add the reset xform button
        reset = wx.Button(self, -1, "reset xform", name="Reset",
                          style=wx.BU_EXACTFIT)

        # Add weight box
        weightsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.weight = NumberTextCtrl(self)
        self.weight.SetAllowedRange(low=0)
        weightsizer.AddMany((wx.StaticText(self, -1, "weight"), self.weight))
        
        

        # Add the Comboboxes and buttons
        map(self.MakeComboBox, *zip(("rotate", 15),
                                    ("translate", 0.1),
                                    ("scale", 1.25)))
        
        btn = [wx.BitmapButton(self, -1, LoadIcon('xformtab',i),
                               name=i.replace("-",""))
               for i in ('90-Left', 'Rotate-Left', 'Rotate-Right', '90-Right',
                         'Move-Up', 'Move-Down', 'Move-Left', 'Move-Right',
                         'Shrink', 'Grow')]
        
        btn.insert(2, self.rotate)
        btn.insert(7, self.translate)
        btn.insert(10, (0,0))
        btn.insert(12, self.scale)
        
        fgs2 = wx.FlexGridSizer(4, 5, 1, 1)
        fgs2.AddMany(btn)        
        
        # Finally, put everything together
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany((hsizer, reset, weightsizer, fgs2))
        self.SetSizer(sizer)
        self.Layout()

        
    def MakeComboBox(self, name, default):
        cb = wx.ComboBox(self, -1, str(default), name=name, size=(80,28),
                         choices=self.choices[name])
        setattr(self, name, cb)
        cb.Bind(wx.EVT_TEXT, functools.partial(self.OnComboChar, cb=cb))
        

    @Bind(wx.EVT_RADIOBUTTON)
    def OnRadioSelected(self,e):
        self._view[1] = e.GetEventObject().GetLabel()
        self.UpdateView()


    @Bind(wx.EVT_CHECKBOX)
    def OnCheckbox(self,e):
        """Toggles post transform selection."""
        self._view[0] = e.IsChecked()
        self.UpdateView()


    def OnComboChar(self, e, cb):
        val = "".join(char for char in e.GetString() if char in "0123456789.-")
        cb.SetValue(val)


    @Bind(wx.EVT_BUTTON)
    def OnButton(self, e):
        for i in "rotate", "translate", "scale":
            cb = getattr(self, i)
            try:
                setattr(self, "_%s" %i, float(cb.GetValue()))
            except:
                cb.SetValue(str(getattr(self, "_%s" %i)))
                
        xform, view = self.GetActive()            
        getattr(self, "Func%s" %e.GetEventObject().GetName())(xform)
        self.parent.TreePanel.TempSave()


    def Funcx(self, xform):
        xform.a, xform.d = 1,0

    def Funcy(self, xform):
        xform.b, xform.e = 0,1

    def Funco(self, xform):
        xform.c, xform.f = 0,0

    def FuncReset(self, xform):
        xform.coefs = 1,0,0,1,0,0

    def Func90Left(self, xform):
        xform.rotate(90)

    def FuncRotateLeft(self, xform):
        xform.rotate(self._rotate)

    def FuncRotateRight(self, xform):
        xform.rotate(-self._rotate)

    def Func90Right(self, xform):
        xform.rotate(-90)

    def FuncMoveUp(self, xform):
        xform.move_pos(0, self._translate)

    def FuncMoveDown(self, xform):
        xform.move_pos(0, -self._translate)

    def FuncMoveLeft(self, xform):
        xform.move_pos(-self._translate, 0)

    def FuncMoveRight(self, xform):
        xform.move_pos(self._translate, 0)

    def FuncShrink(self, xform):
        xform.scale(1.0/self._scale)

    def FuncGrow(self, xform):
        xform.scale(self._scale)


    def GetActive(self):
        post, view = self._view
        xform = self.parent.ActiveXform
        if post:
            xform = xform.post
        return xform, view


    def UpdateView(self):
        xform, view = self.GetActive()

        # Update weight tc.
        if xform.ispost():
            self.weight.Disable()
            self.weight.SetValue("--")
        else:
            self.weight.Enable()
            self.weight.SetFloat(xform.weight)
            
        if view == "triangle":
            self.coefs = itertools.chain(*xform.points)
        elif view == "xform":
            self.coefs = xform.coefs
        elif view == "polar":
            self.coefs = itertools.chain(*xform.polars)

        font = self.postflag.GetFont()
        post = xform if xform.ispost() else xform.post
        if post.isactive():
            font.Weight = wx.FONTWEIGHT_BOLD
        else:
            font.Weight = wx.FONTWEIGHT_NORMAL
        self.postflag.SetFont(font)


    def UpdateXform(self,e=None):
        xform, view = self.GetActive()

        # Update weight.
        if not xform.ispost():
            xform.weight = self.weight.GetFloat()

        if view == "triangle":
            xform.points = zip(*[iter(self.coefs)]*2)
        elif view == "xform":
            xform.coefs = self.coefs
        elif view == "polar":
            xform.polars = zip(*[iter(self.coefs)]*2)
            
        self.parent.TreePanel.TempSave()
                                          

    def _get_coefs(self):
        return (getattr(self,i).GetFloat() for i in "adbecf")

    def _set_coefs(self,v):
        map(lambda x,y: getattr(self,x).SetFloat(y), "adbecf", v)

    coefs = property(_get_coefs, _set_coefs)



class VarPanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent.parent

        self.tree = gizmos.TreeListCtrl(self, -1, style =
                                          wx.TR_DEFAULT_STYLE
                                        | wx.TR_ROW_LINES
                                        | wx.TR_COLUMN_LINES
                                        | wx.TR_NO_LINES
                                        | wx.TR_HIDE_ROOT
                                        | wx.TR_FULL_ROW_HIGHLIGHT
                                   )

        _ = gizmos.TreeListCtrl(self, -1)

        self.tree.AddColumn("Var")
        self.tree.AddColumn("Value")

##        self.tree.SetMainColumn(0)
        self.tree.SetColumnWidth(0, 160)
        self.tree.SetColumnWidth(1, 60)
        self.tree.SetColumnEditable(1,True)

        self.root = self.tree.AddRoot("The Root Item")
        self.item = self.root

        for i in config["active-vars"]:
            child = self.tree.AppendItem(self.root, i)

            for j in pyflam3.variables[i]:
                item = self.tree.AppendItem(child,  j)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree,1,wx.EXPAND)
        self.SetSizer(sizer)

        window = self.tree.GetMainWindow()
        window.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        window.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        window.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        window.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.HasChanged = False


    def itervars(self, item=None):
        if not item:
            item = self.root
        child,cookie = self.tree.GetFirstChild(item)  
        while child.IsOk():
            name = self.tree.GetItemText(child)
            yield (child, name)
            for i,_ in self.itervars(child):
                yield (i, "%s_%s" % (name, self.tree.GetItemText(i)))
            child,cookie = self.tree.GetNextChild(item,cookie)


    def UpdateView(self):
        xform = self.parent.ActiveXform
        for i,name in self.itervars():
            attr = str(getattr(xform, name))
            if self.tree.GetItemText(i,1) == attr:
                continue
            self.tree.SetItemText(i, attr, 1)


    def SetFlameAttribute(self, item, value):
        parent = self.tree.GetItemParent(item)
        if parent == self.root:
            # it's a variation
            name = self.tree.GetItemText(item, 0)
        else:
            # it's a variable
            name = "_".join(map(self.tree.GetItemText,(parent,item)))
        setattr(self.parent.ActiveXform,name,value)
        # TODO: This could be optimized to just redraw the var preview.
        self.parent.canvas.ShowFlame(rezoom=False)


    @Bind(wx.EVT_TREE_END_LABEL_EDIT)
    def OnEndEdit(self, e):
        item = e.GetItem()
        oldvalue = self.tree.GetItemText(item, 1)
        try:
            value = float(e.GetLabel() or "0.0")
            self.tree.SetItemText(item,str(value),1)
        except ValueError:
            e.Veto()
            return

        if value != oldvalue:
            self.SetFlameAttribute(item, value)
            self.parent.TreePanel.TempSave()

        e.Veto()


##    # TODO: is it preferrable to have:
##    #   -ITEM_ACTIVATED: ability to search with letters.
##    #   -SEL_CHANGED:    immediate edit of values
##    # TODO: Need to test this under win!
####    @Bind(wx.EVT_TREE_ITEM_ACTIVATED)

    
    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self,e):
        """Makes sure the tree always knows what item is selected."""
        self.item = e.GetItem()
        

    def OnKeyDown(self ,e):
        key = e.GetKeyCode()
        if key in (wx.WXK_NUMPAD_ENTER, wx.WXK_RETURN):
            self.tree.EditLabel(self.item, 1)
            self._editing = True
        else:
            e.Skip()
            

    def OnLeftDClick(self, e):
        # HACK: col is either -1 or 1. I don't know what the 2 param is.
        item, _, col =  self.tree.HitTest(e.Position)
        if col == 1:
            self.tree.EditLabel(item, 1)
        elif col == -1:
            text = self.tree.GetItemText(item, 1)
            if text == '0.0':
                new = 1.0
            else:
                new = 0.0
            self.SetFlameAttribute(item, new)
            self.tree.SetItemText(item, str(new), 1)
            self.parent.TreePanel.TempSave()
        e.Skip()
        

    def OnWheel(self,e):
        if e.ControlDown():
            if e.AltDown():
                diff = 0.01
            else:
                diff = 0.1
        elif e.AltDown():
            diff = 0.001
        else:
            e.Skip()
            return

        self.SetFocus() # Makes sure OnKeyUp gets called.
        
        item = self.tree.HitTest(e.GetPosition())[0]
        try:
            name = self.tree.GetItemText(item)
        except wx.PyAssertionError:
            # Widget may have focus when mouse is elsewhere.
            return
        val = self.tree.GetItemText(item, 1) or "0.0"
        
        val = float(val) + (diff if e.GetWheelRotation() > 0 else -diff)
        self.SetFlameAttribute(item, val)
        self.tree.SetItemText(item, str(val), 1)
        self.parent.image.RenderPreview()
        self.HasChanged = True
        

    def OnKeyUp(self, e):
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TreePanel.TempSave()
                self.HasChanged = False



class ColorPanel(MultiSliderMixin, wx.Panel):

    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        super(ColorPanel, self).__init__(parent, -1)

        self.bmp = wx.EmptyBitmap(128, 28)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((198,50))
        sizer.AddMany((self.MakeSlider(*i), 0, wx.EXPAND) for i in
                      (("color", 0, 0, 1),
                       ("symmetry", 0, -1, 1),
                       ("opacity", 1, 0, 1)))

        self.SetSizer(sizer)


    def UpdateView(self):
        flame = self.parent.flame
        xform = self.parent.ActiveXform

        for name in self.sliders:
            self.UpdateSlider(name, getattr(xform, name))         
        
        color = int(xform.color * 256) or 1
        grad = itertools.chain(*flame.gradient[:color])
        buff = "%c%c%c" * color % tuple(map(int, grad))
        img = wx.ImageFromBuffer(color, 1, buff)
        img.Rescale(192, 28) # Could be 128, 192 or 256
        self.bmp = wx.BitmapFromImage(img)
        self.Refresh()


    def UpdateXform(self):
        # Note: This method is also called by OnIdle.
        for name, val in self.IterSliders():
            setattr(self.parent.ActiveXform, name, val)
        self.UpdateView()
        self.parent.image.RenderPreview() 


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 2, 2, True)     



class ChaosPanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent.parent

        self.tree1 = self.init_tree("To")
        self.tree2 = self.init_tree("From")
        _ = gizmos.TreeListCtrl(self, -1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.tree1, 1, wx.EXPAND)
        sizer.Add(self.tree2, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.HasChanged = False


    def init_tree(self, label):

        tree = gizmos.TreeListCtrl(self, -1, style =
                                          wx.TR_DEFAULT_STYLE
                                        | wx.TR_ROW_LINES
                                        | wx.TR_COLUMN_LINES
                                        | wx.TR_NO_LINES
                                        | wx.TR_HIDE_ROOT
                                        | wx.TR_FULL_ROW_HIGHLIGHT
                                        | wx.NO_BORDER
                                   )
        
        tree.AddColumn(label)
        tree.AddColumn("Value")
        tree.SetColumnWidth(0, 50)
        tree.SetColumnWidth(1, 60)
        tree.SetColumnEditable(1,True)
        tree.AddRoot("The Root Item")

        window = tree.GetMainWindow()
        window.Bind(wx.EVT_MOUSEWHEEL, partial(self.OnWheel, tree))
        window.Bind(wx.EVT_KEY_UP, partial(self.OnKeyUp, tree))
        window.Bind(wx.EVT_LEFT_DCLICK, partial(self.OnLeftDClick, tree))
        window.Bind(wx.EVT_KEY_DOWN, partial(self.OnKeyDown, tree))
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, partial(self.OnEndEdit, tree),
                  tree)
        
        return tree
    
        
    def IterTree(self, tree):
        root = tree.GetRootItem()
        child, cookie = tree.GetFirstChild(root)
        while child.IsOk():
            yield child
            child, cookie = tree.GetNextChild(root, cookie)        


    def BuildTrees(self, count):
        for tree in (self.tree1, self.tree2):
            i = 1
            for child in list(self.IterTree(tree)):
                if i > count:
                    tree.Delete(child)
                i += 1
            while i <= count:
                item = tree.AppendItem(tree.GetRootItem(), str(i))
                i += 1


    def UpdateView(self):
        tree1, tree2 = self.tree1, self.tree2
        xform = self.parent.ActiveXform
        if xform.isfinal():
            self.BuildTrees(0)
            return
        self.BuildTrees(len(self.parent.flame.xform))

        index = xform.index        
        for i, val in zip(self.IterTree(tree1), xform.chaos):
            new = str(val)
            if self.tree1.GetItemText(i,1) != new:
                self.tree1.SetItemText(i, new, 1)
                
        for i, xf in zip(self.IterTree(tree2), self.parent.flame.xform):
            new = str(xf.chaos[index])
            if self.tree2.GetItemText(i,1) != new:
                self.tree2.SetItemText(i, new, 1)            


    def SetFlameAttribute(self, tree, item, value):
        if value < 0:
            value = 0
            tree.SetItemText(item, "0.0", 1)
        active = self.parent.ActiveXform
        index = int(tree.GetItemText(item, 0)) -1
        if tree == self.tree2:
            self.parent.flame.xform[index].chaos[active.index] = value
        else:
            active.chaos[index] = value


    def OnEndEdit(self, tree, e):
        item = e.GetItem()
        oldvalue = tree.GetItemText(item, 1)
        try:
            value = float(e.GetLabel() or "0.0")
            tree.SetItemText(item, str(value), 1)
        except ValueError:
            e.Veto()
            return

        if value != oldvalue:
            self.SetFlameAttribute(tree, item, value)
            self.parent.TreePanel.TempSave()

        e.Veto()


    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self,e):
        """Makes sure the tree always knows what item is selected."""
        self.item = e.GetItem()
        

    def OnKeyDown(self, tree, e):
        key = e.GetKeyCode()
        if key in (wx.WXK_NUMPAD_ENTER, wx.WXK_RETURN):
            tree.EditLabel(self.item, 1)
        else:
            e.Skip()
            

    def OnLeftDClick(self, tree, e):
        item, _, col =  tree.HitTest(e.Position)
        if col == 1:
            tree.EditLabel(item, 1)
        else:
            text = tree.GetItemText(item, 1)
            new = 1.0 if text == '0.0' else 0.0
            tree.SetItemText(item, str(new), 1)
            self.SetFlameAttribute(tree, item, new)
            self.parent.TreePanel.TempSave()
        e.Skip()
        

    def OnWheel(self, tree, e):
        if e.ControlDown():
            if e.AltDown():
                diff = 0.01
            else:
                diff = 0.1
        elif e.AltDown():
            diff = 0.001
        else:
            e.Skip()
            return

        self.SetFocus() # Makes sure OnKeyUp gets called.
        
        item = tree.HitTest(e.GetPosition())[0]
        name = tree.GetItemText(item)
        val = tree.GetItemText(item, 1) or "0.0"
        
        val = float(val) + (diff if e.GetWheelRotation() > 0 else -diff)
        tree.SetItemText(item, str(val), 1)
        self.SetFlameAttribute(tree, item, val)
        self.parent.image.RenderPreview()
        self.HasChanged = True
        

    def OnKeyUp(self, tree, e):
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TreePanel.TempSave()
                self.HasChanged = False
    
