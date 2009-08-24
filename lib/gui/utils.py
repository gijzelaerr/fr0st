import wx, os

def LoadIcon(*path):
    img = wx.Image(os.path.join('lib','gui','icons',*path) + '.png',
                                type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16,16)
    return wx.BitmapFromImage(img)


class DynamicDialog(wx.Dialog):
    """A dialog class used for interactive script input."""
    def __init__(self, parent, result, title, intro, *args):
        wx.Dialog.__init__(self, parent)
        self.Title = title
        szrgs = 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5
        fgs = wx.FlexGridSizer(99, 2, 1, 1)

        widgets = []
        for name, default in args:    
            fgs.Add(wx.StaticText(self, -1, name), *szrgs)

            if type(default) == type:
                type_ = default
                default = None
            else:
                type_ = type(default)

            if type_ == bool:
                widget = wx.CheckBox(self, -1)
                if default:
                    widget.SetValue(True)
            elif type_ in (list, tuple):
                widget = ValidChoice(self, choices=default)
            else:
                widget = ValidTextCtrl(self, type_, default)
            widgets.append(widget)
            fgs.Add(widget, 0, wx.ALIGN_LEFT, 5)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0,10))
        sizer.Add(wx.StaticText(self, -1, intro), *szrgs)
        sizer.Add((0,10))
        sizer.Add(fgs)
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.ShowModal()

        result.extend(w.GetValue() for w in widgets)


class ValidTextCtrl(wx.TextCtrl):
    def __init__(self, parent, type_, default):
        wx.TextCtrl.__init__(self, parent, -1)
        self.type = type_
        if default:
            self.AppendText(str(default))
        else:
            default = type_()
        self.default = default
        if type_ is str:
            minwidth = 200
        else:
            minwidth = 100
        self.SetMinSize((minwidth, 27))

        
    def GetValue(self):
        try:
            return self.type(wx.TextCtrl.GetValue(self))
        except:
            return self.default


class ValidChoice(wx.Choice):
    def __init__(self, parent, choices):
        self.types = map(type, choices)
        self.choices = choices
        self.index = 0
        wx.Choice.__init__(self, parent, -1, choices=map(str, choices))
        self.Bind(wx.EVT_CHOICE, self.OnChoice)

    def GetValue(self):
        return self.choices[self.index]

    def OnChoice(self, e):
        self.index = e.GetInt()
        
