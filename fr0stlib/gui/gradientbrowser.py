import os, re, wx
import xml.etree.cElementTree as etree
import wx.combo
from  wx.lib.filebrowsebutton import FileBrowseButton

from fr0stlib import Palette, load_flamestrings
from fr0stlib.gui.utils import Box, ErrorMessage
from fr0stlib.gui.config import config


class GradientBrowser(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent

        mask = ("Gradient Files (*.ugr)|*.ugr|"
                "Map Files (*.map)|*.map|"
                "Flame Files (*.flame)|*.flame|"
                "All files (*.*)|*.*")

        path = os.path.abspath(config["flamepath"])
        self.fbb = FileBrowseButton(self, -1, fileMask=mask, labelText='File:',
                                    changeCallback=self.fbb_callback,
                                    initialValue=path)
             
        self.bcb = wx.combo.BitmapComboBox(self, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnCombo, self.bcb)

        self.load(path)

        szr = Box(self, "Gradient Browser", (self.fbb, 0, wx.EXPAND|wx.ALL, 5),
                                            (self.bcb, 0, wx.EXPAND|wx.ALL, 5))
        self.SetSizerAndFit(szr)


    def load(self, path):
        self.palettes = []
        self.bcb.Clear()
        
        gen = self.parse_file(path)
        if gen is None:
            # NOTE: this can mean that the file extension isn't recognized, or
            # that the re/parsing/etc found nothing in the file.
            return
        
        for name, palette in gen:
            img = wx.ImageFromBuffer(256, 1, palette.to_buffer())
            img.Rescale(128, 20)
            bmp = wx.BitmapFromImage(img)
            self.bcb.Append(name, bmp)
            self.palettes.append(palette)

        self.bcb.Select(0)


    def parse_file(self, path):
        if not os.path.exists(path):
            return
        ext = os.path.splitext(path)[1]
        if ext in (".flame", ".bak"):
            return ((re.search(' name="(.*?)"', string).group(1),
                     Palette(etree.fromstring(string)))
                    for string in load_flamestrings(path))
        if ext in (".map"):
            with open(path,'r') as mf:
                lns = mf.readlines()

            P = Palette()
            P.from_strings(lns)
            return ((os.path.splitext(os.path.basename(path))[0], P),)
        

    def OnCombo(self, e):
        if not self.palettes:
            return
        self.parent.parent.flame.gradient[:] = self.palettes[e.Int][:]
        self.parent.parent.TempSave()


    def fbb_callback(self, e):
        self.load(e.String)
        if not self.palettes:
            ErrorMessage(self, "%s is not a valid gradient file." % e.String)
        
