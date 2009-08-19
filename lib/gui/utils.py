import wx, os


def LoadIcon(*path):
    img = wx.Image(os.path.join('lib','gui','icons',*path) + '.png',
                                type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16,16)
    return wx.BitmapFromImage(img)


class DynamicDialog(wx.Dialog):
    """A dialog class used for interactive script input."""


    def __init__(self, parent, result, title, intro, *args):
        wx.Dialog.__init__(self, parent, size=wx.DefaultSize)
        self.Title = title
        szrgs = 0, wx.ALIGN_CENTRE|wx.ALL, 5
        fgs = wx.FlexGridSizer(99, 2, 1, 1)

        widgets = []
        for name, default in args:    
            fgs.Add(wx.StaticText(self, -1, name), 0,
                    wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)

            if type(default) == type:
                type_ = default
                default = None
            else:
                type_ = type(default)

            if type_ == bool:
                widget = wx.CheckBox(self, -1)
                if default:
                    widget.SetValue(True)
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
        sizer.Add(wx.StaticText(self, -1, intro), *szrgs)
        sizer.Add(fgs)
        sizer.Add(btnsizer, *szrgs)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.ShowModal()

        result.extend(w.GetValue() for w in widgets)


class ValidTextCtrl(wx.TextCtrl):
    def __init__(self, parent, type, default):
        wx.TextCtrl.__init__(self, parent, -1)
        self.default = default
        self.type = type
        if default:
            self.AppendText(str(default))
        
    def GetValue(self):
        try:
            return self.type(wx.TextCtrl.GetValue(self))
        except:
            return self.default

