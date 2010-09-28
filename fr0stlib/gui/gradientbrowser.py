import os, re, wx
import xml.etree.cElementTree as etree
import wx.combo
from  wx.lib.filebrowsebutton import FileBrowseButton

from fr0stlib import Palette, load_flamestrings
from fr0stlib.gui.utils import Box
from fr0stlib.gui.config import config


class GradientBrowser(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent

        mask = "Flame Files (*.flame)|*.flame|" \
               "Gradient Files (*.ugr)|*.ugr|" \
               "Map Files (*.map)|*.map"

        path = os.path.abspath(config["flamepath"])
        self.fbb = FileBrowseButton(self, -1, fileMask=mask,
                                    labelText='File:', initialValue=path,
                                    changeCallback=self.fbb_callback)
             
        self.bcb = wx.combo.BitmapComboBox(self, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnCombo, self.bcb)

        self.load(path)

        szr = Box(self, "Gradient Browser", (self.fbb, 0, wx.EXPAND|wx.ALL, 5),
                                            (self.bcb, 0, wx.EXPAND|wx.ALL, 5))
        self.SetSizerAndFit(szr)


    def load(self, path):
        self.palettes = []
        self.bcb.Clear()

        for name, palette in self.parse_file(path):
            img = wx.ImageFromBuffer(256, 1, palette.to_buffer())
            img.Rescale(128, 20)
            bmp = wx.BitmapFromImage(img)
            self.bcb.Append(name, bmp)
            self.palettes.append(palette)

        self.bcb.Select(0)


    def parse_file(self, path):
        ext = os.path.splitext(path)[1]
        if ext == ".flame":
            return ((re.search(' name="(.*?)"', string).group(1),
                     Palette(etree.fromstring(string)))
                    for string in load_flamestrings(path))


    def OnCombo(self, e):
        self.parent.parent.flame.gradient[:] = self.palettes[e.Int][:]
        self.parent.parent.TempSave()


    def fbb_callback(self, e):
        self.load(e.String)
        
