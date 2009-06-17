import wx, os, functools, itertools
from wx import gizmos
from collections import defaultdict

from decorators import Bind,BindEvents
from lib.fr0stlib import polar, rect
from lib import pyflam3
from lib.gui.config import config


def LoadIcon(name):
    img = wx.Image(os.path.join('lib','gui','icons','xformtab',"%s.png" %name),
                                type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16, 16)
    return wx.BitmapFromImage(img)


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

        self.Xform = XformPanel(self)
        self.AddPage(self.Xform, "Xform")

        self.Vars = VarPanel(self)
        self.AddPage(self.Vars, "Vars")

        self.Color = ColorPanel(self)
        self.AddPage(self.Color, "Color")

        win = wx.Panel(self, -1)
        self.AddPage(win, "Xaos")

        self.Selector = wx.Choice(self.parent, -1)
        self.Selector.Bind(wx.EVT_CHOICE, self.OnChoice)

        self.SetMinSize((262,100))


    def UpdateView(self):
        for i in self.Xform, self.Vars, self.Color:
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
        
        btn = [wx.BitmapButton(self, -1, LoadIcon(i), name=i.replace("-",""))
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
        xform.move_position(0, self._translate)

    def FuncMoveDown(self, xform):
        xform.move_position(0, -self._translate)

    def FuncMoveLeft(self, xform):
        xform.move_position(-self._translate, 0)

    def FuncMoveRight(self, xform):
        xform.move_position(self._translate, 0)

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

        # Update weight. If more values are ever needed here, write a
        # get/setattr loop.
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

#------------------------------------------------------------------------------

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

        self.tree.AddColumn("Var")
        self.tree.AddColumn("Value")

        self.tree.SetMainColumn(0)
        self.tree.SetColumnWidth(0, 160)
        self.tree.SetColumnWidth(1, 60)
        self.tree.SetColumnEditable(1,True)

        self.root = self.tree.AddRoot("The Root Item")

        for i in config["active_vars"]:
            child = self.tree.AppendItem(self.root, i)

            for j in pyflam3.variables[i]:
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
        xform = self.parent.ActiveXform
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
        setattr(self.parent.ActiveXform,name,value)


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
                diff = 0.01
            else:
                diff = 0.1
        elif e.AltDown():
            diff = 0.001
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
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TreePanel.TempSave()
                self.HasChanged = False
            

class NumberTextCtrl(wx.TextCtrl):
    low = None
    high = None

    @BindEvents
    def __init__(self, parent):
        self.parent = parent
        # Size is set to ubuntu default (75,27), maybe make it 75x21 in win
        wx.TextCtrl.__init__(self,parent,-1, size=(75,27))
        self.SetValue("0.0")
        self._value = 0.0

    def GetFloat(self):
        return float(self.GetValue() or "0")

    def SetFloat(self,v):
        # Make sure pure ints don't make trouble
        v = float(v)

        self._value = v
        
        # Avoid exponent notation
        if abs(v) < 1E-04:
            if abs(v) < 1E-06:
                string = "0.0"
            else:
                string = ("%f" %v).rstrip("0")
        else:
            string = str(v)
        
        self.SetValue(string)


    def SetAllowedRange(self, low=None, high=None):
        self.low = low
        self.high = high


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
        # This comparison is done with strings because the floats don't
        # always compare equal (!)
        if str(self._value) != self.GetValue():
            try:
                v = self.GetFloat() # Can raise ValueError
                if self.low is not None and v < self.low:
                    raise ValueError
                if self.high is not None and v > self.high:
                    raise ValueError
                self._value = v
                self.parent.UpdateXform()
            except ValueError:
                self.SetFloat(self._value)
        

#------------------------------------------------------------------------------


class ColorPanel(wx.Panel):
    _new = None

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent.parent

        self.bmp = wx.EmptyBitmap(128, 28)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((198,50))
        sizer.AddMany((self.MakeSlider(*i), 0, wx.EXPAND) for i in
                      (("Color",), ("Symmetry", 0, -100), ("Opacity", 100)))

        self.SetSizer(sizer)


    def MakeSlider(self, name, init=0, low=0, high=100):
        """Programatically builds stuff."""
        slider = wx.Slider(self, -1, init, low, high,
                           style=wx.SL_HORIZONTAL
                           |wx.SL_AUTOTICKS
                           |wx.SL_LABELS)
        tc = NumberTextCtrl(self)
        tc.SetAllowedRange(low/100., high/100.)
        setattr(self, "%sslider" %name, slider)
        setattr(self, "%stc" %name, tc)

        slider.Bind(wx.EVT_SLIDER, functools.partial(self.OnSlider, name=name))
##        slider.Bind(wx.EVT_LEFT_DOWN, self.OnSliderDown)
        slider.Bind(wx.EVT_LEFT_UP, self.OnSliderUp)

        siz = wx.StaticBoxSizer(wx.StaticBox(self, -1, name), wx.HORIZONTAL)
        siz.Add(tc)
        siz.Add(slider, wx.EXPAND)

        return siz
        

    def UpdateView(self):
        flame = self.parent.flame
        xform = self.parent.ActiveXform

        for name in "Color", "Symmetry", "Opacity":
            val = getattr(xform, name.lower())
            getattr(self, "%sslider" %name).SetValue(val*100)
            getattr(self, "%stc" %name).SetFloat(val)
        
        color = int(xform.color * 256)

        if color:
            grad = itertools.chain(*flame.gradient[:color])
            buff = "%c%c%c" * color % tuple(grad)
            img = wx.ImageFromBuffer(color, 1, buff)
        else:
            img = wx.ImageFromBuffer(1, 1, "%c%c%c" %flame.gradient[0])
            
        img.Rescale(192, 28) # Could be 128, 192 or 256
        self.bmp = wx.BitmapFromImage(img)
        self.Refresh()


    def UpdateXform(self):
        """This method is called by the tcs."""
        for i in "Color", "Symmetry", "Opacity":
            val = getattr(self, "%stc" %i).GetFloat()
            setattr(self.parent.ActiveXform, i.lower(), val)        
        self.UpdateView()
        self.parent.image.RenderPreview() 


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 2, 2, True)


    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        if self._new is not None:
            self.UpdateXform()
            self._new = None
            self._changed = True       


    def OnSlider(self, e, name):
        val = e.GetInt()/100.
        tc = getattr(self, "%stc" %name)
        # Make sure _new is only set when there are actual changes.
        if val != tc._value:
            self._new = True
            tc.SetFloat(str(val))
        e.Skip()

     
##    def OnSliderDown(self, e):
##        e.Skip()


    def OnSliderUp(self, e):
        if self._changed:
            self.parent.TreePanel.TempSave()
            self._changed = False
        e.Skip()
        
