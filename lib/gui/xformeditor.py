import wx
from wx import gizmos
import wx.lib.customtreectrl as CT
from itertools import chain
from collections import defaultdict

from decorators import Bind,BindEvents
from lib.functions import polar, rect
from lib import pyflam3


class XformTabs(wx.Notebook):

    def __init__(self, parent):
        self.parent = parent
        wx.Notebook.__init__(self, parent, -1, size=(21,21), style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )

        self.Vars = VarPanel(self)
        self.AddPage(self.Vars, "Vars")
        
        self.Xform = XformPanel(self)
        self.AddPage(self.Xform, "Xform")

        win = wx.Panel(self, -1)
        self.AddPage(win, "Color")

        win = wx.Panel(self, -1)
        self.AddPage(win, "Xaos")

    def UpdateView(self):
        for i in self.Xform, self.Vars:
            i.UpdateView()


            

class XformPanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        # The view tells us what attributes need to be displayed
        self.view = [False, "triangle"]
        self.parent = parent.parent

        # Add the number fields
        map(lambda x: setattr(self,x,NumberTextCtrl(self)),"abcdef")
        map(lambda x: setattr(self,x,wx.Button(self,-1,x,style=wx.BU_EXACTFIT)),
            "xyo")

        fgs = wx.FlexGridSizer(3,3,1,1)
        fgs.AddMany(map(self.__getattribute__,"xadybeocf"))

        reset = wx.Button(self,-1,"reset xform", style=wx.BU_EXACTFIT)
        r1 = wx.RadioButton(self, -1, "triangle", style = wx.RB_GROUP )
        r2 = wx.RadioButton(self, -1, "xform" )
        r3 = wx.RadioButton(self, -1, "polar" )
        postflag = wx.CheckBox(self,-1,"post")

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddMany((r1,r2,r3,postflag))

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddMany((fgs,vsizer))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany((hsizer,reset))
        self.SetSizer(sizer)
        self.Layout()

    @Bind(wx.EVT_RADIOBUTTON)
    def OnRadioSelected(self,e):
        self.view[1] = e.GetEventObject().GetLabel()
        self.UpdateView()


    @Bind(wx.EVT_CHECKBOX)
    def OnPostCheckbox(self,e):
        self.view[0] = e.IsChecked()
        self.UpdateView()

        
    def UpdateView(self):
        post, view = self.view
        xform = self.parent.canvas.ActiveXform
        if post:
            xform = xform.post
            
        if view == "triangle":
            self.coefs = chain(*xform.points)
        elif view == "xform":
            self.coefs = xform.coefs
        elif view == "polar":
            self.coefs = chain(*map(polar, zip(*[iter(xform.coefs)]*2)))


    def UpdateXform(self,e=None):
        post, view = self.view
        xform = self.parent.canvas.ActiveXform
        if post:
            xform = xform.post

        if view == "triangle":
            xform.points = zip(*[iter(self.coefs)]*2)
        elif view == "xform":
            xform.coefs = self.coefs
        elif view == "polar":
            xform.coefs = chain(*map(rect, *[iter(self.coefs)]*2))

        self.parent.TreePanel.TempSave()
                                          

    def _get_coefs(self):
        return (getattr(self,i).GetFloat() for i in "adbecf")

    def _set_coefs(self,v):
        map(lambda x,y: getattr(self,x).SetFloat(y),"adbecf",v)

    coefs = property(_get_coefs, _set_coefs)


class VarPanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent.parent

        # Variations are sorted by their index, i.e. their dict value, not key.
        gen = ((j,i) for i,j in pyflam3.variations.items())
        self.variations = [i for j,i in sorted(gen)]
        self.variables = defaultdict(list)
        for i in dir(pyflam3.BaseXForm):
            lst = i.split("_",1)
            if lst[0] in self.variations:
                self.variables[lst[0]].append(lst[1])

        # TODO: find a way to actually filter out all variables

        self.tree = gizmos.TreeListCtrl(self, -1, style =
                                          wx.TR_DEFAULT_STYLE
                                        | wx.TR_ROW_LINES
                                        | wx.TR_COLUMN_LINES
                                        | wx.TR_NO_LINES
                                        | wx.TR_HIDE_ROOT
                                        | wx.TR_FULL_ROW_HIGHLIGHT
                                   )

        self.tree.AddColumn("Var")
        self.tree.AddColumn("Value")

        self.tree.SetMainColumn(0)
        self.tree.SetColumnWidth(0, 165)
        self.tree.SetColumnWidth(1, 64)
        self.tree.SetColumnEditable(1,True)

        self.root = self.tree.AddRoot("The Root Item")

        for i in self.variations:
            child = self.tree.AppendItem(self.root, i)

            for j in self.variables[i]:
                item = self.tree.AppendItem(child,  j)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree,1,wx.EXPAND)
        self.SetSizer(sizer)

        self.tree.GetMainWindow().Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.parent.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
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
        xform = self.parent.canvas.ActiveXform
        for i,name in self.itervars():
            self.tree.SetItemText(i, str(getattr(xform, name)), 1)


    def SetFlameAttribute(self, item, value):
        parent = self.tree.GetItemParent(item)
        if parent == self.root:
            # it's a variation
            name = self.tree.GetItemText(item, 0)
        else:
            # it's a variable
            name = "_".join(map(self.tree.GetItemText,(parent,item)))
        setattr(self.parent.canvas.ActiveXform,name,value)


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


    # TODO: is it preferrable to have:
    #   -SEL_CHANGED:    immediate edit of values
    #   -ITEM_ACTIVATED: ability to search with letters.
    @Bind(wx.EVT_TREE_ITEM_ACTIVATED)
##    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self,e):
        item = e.GetItem()
        if item != self.root:
            self.tree.EditLabel(item,1)
        e.Veto()


    def OnWheel(self,e):
        if e.ControlDown():
            if e.AltDown():
                diff = 0.001
            else:
                diff = 0.1
        elif e.AltDown():
            diff = 0.01
        else:
            e.Skip()
            return

        self.SetFocus() # Makes sure OKeyUp gets called.
        
        item = self.tree.HitTest(e.GetPosition())[0]
        name = self.tree.GetItemText(item)
        val = self.tree.GetItemText(item, 1) or "0.0"
        
        val = float(val) + (diff if e.GetWheelRotation() > 0 else -diff)
        self.SetFlameAttribute(item, val)
        self.tree.SetItemText(item, str(val), 1)
        self.parent.image.RenderPreview()
        self.HasChanged = True
        

    def OnKeyUp(self, e):
        key = e.GetKeyCode()
        print key == wx.WXK_CONTROL, key == wx.WXK_ALT
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TreePanel.TempSave()
                self.HasChanged = False
            

class NumberTextCtrl(wx.TextCtrl):

    @BindEvents
    def __init__(self,parent):
        self.parent = parent
        # Size is set to ubuntu default, maybe make it 75x21 in win only
        wx.TextCtrl.__init__(self,parent,-1, size=(75,27))
        self.SetValue("0.0")
        self._value = 0.0

    def GetFloat(self):
        return float(self.GetValue() or "0")

    def SetFloat(self,v):
        v = float(v) # Make sure pure ints don't make trouble
        self.SetValue(str(v))
        self._value = v


    @Bind(wx.EVT_CHAR)
    def OnChar(self, event):
        key = event.GetKeyCode()

        if key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            self.OnKillFocus(None)
            
        elif key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()

        elif chr(key) in "0123456789.-":
            event.Skip()

        else:
            # not calling Skip() eats the event
            pass #wx.Bell()


    @Bind(wx.EVT_KILL_FOCUS)
    def OnKillFocus(self,event):
        val = self.GetFloat()
        if not val:
            self.SetFloat(0.0)
            # This comparison is done with strings because the floats don't
            # always compare equal (!)
        if str(self._value) != str(val):
            self._value = val
            self.parent.UpdateXform()

