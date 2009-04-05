import wx
from itertools import chain

from decorators import Bind,BindEvents
from lib.functions import polar, rect


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

        win = wx.Panel(self, -1)
        self.AddPage(win, "Vars")
        
        self.Xform = XformPanel(self)
        self.AddPage(self.Xform, "Xform")

        win = wx.Panel(self, -1)
        self.AddPage(win, "Color")

        win = wx.Panel(self, -1)
        self.AddPage(win, "Xaos")

    def UpdateView(self):
        self.Xform.UpdateView()


class NumberTextCtrl(wx.TextCtrl):

    @BindEvents
    def __init__(self,parent):
        self.parent = parent
        wx.TextCtrl.__init__(self,parent,-1)
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
        xform = self.parent.flame.xform[0]
        if post:
            xform = xform.post
            
        if view == "triangle":
            self.coefs = chain(xform.x,xform.y,xform.o)
        elif view == "xform":
            self.coefs = xform.coefs
        elif view == "polar":
            self.coefs = chain(*map(polar, zip(*[iter(xform.coefs)]*2)))


    def UpdateXform(self,e=None):
        post, view = self.view
        xform = self.parent.flame.xform[0]
        if post:
            xform = xform.post

        if view == "triangle":
            xform.x,xform.y,xform.o = zip(*[iter(self.coefs)]*2)
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
            

