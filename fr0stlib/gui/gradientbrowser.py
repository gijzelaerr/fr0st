import os, re, wx
import xml.etree.cElementTree as etree
import wx.combo
from  wx.lib.filebrowsebutton import FileBrowseButton

from fr0stlib import Palette, load_flamestrings
from fr0stlib.gui.utils import Box, ErrorMessage
from fr0stlib.gui.config import config

# support for ugr palettes - thx bobby
_ugr_main_re = re.compile(
        '\s*(.*?)\s*{\s*gradient:\s*title="(.*?)"\s*smooth=(yes|no)\s*(.*?)\}', 
        re.DOTALL)

_ugr_inner_re = re.compile('\s*index=(\d+)\s*color=(\d+)')

def _blend_palette(palette, begin, end):
    if begin == end:
        return

    idx_range = float(end - begin)
    end_idx = end % 256
    begin_idx = begin % 256

    for c_idx in range(3):
        color_range = float(palette[end_idx][c_idx]) - float(palette[begin_idx][c_idx])
        c = palette[begin_idx][c_idx]
        v = color_range / idx_range

        for interp_idx in range(begin +1, end):
            c += v
            palette[interp_idx % 256][c_idx] = c

def _load_ugr_iter(filename):
    with open(filename) as  gradient_fd:
        text = gradient_fd.read()

    index_ratio = 255.0 / 399.0
    
    for match in _ugr_main_re.finditer(text):
        item_name, title, smooth, inner = match.groups()
        palette = Palette()
    
        indices = []
        for index, color in _ugr_inner_re.findall(inner):
            # -401 being a legal index is just stupid...
            while index < 0:
                index += 400
    
            index = int(index)
            index = int(round(index * index_ratio))
            indices.append(index)
            color = int(color)
    
            r = (color & 0xFF0000) >> 16
            g = (color & 0xFF00) >> 8
            b = (color & 0xFF)

            print index,r,g,b  

            palette[index] = (r, g, b)
   
        for idx in range(len(indices) - 1):
            x, y = indices[idx], indices[idx+1]
            _blend_palette(palette, indices[idx], indices[idx+1])
    
        _blend_palette(palette, indices[-1], indices[0] + 256)

        yield (title,palette)


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
        if ext in (".ugr"):
            return list(_load_ugr_iter(path))
        

    def OnCombo(self, e):
        if not self.palettes:
            return
        self.parent.parent.flame.gradient[:] = self.palettes[e.Int][:]
        self.parent.parent.TempSave()


    def fbb_callback(self, e):
        self.load(e.String)
        if not self.palettes:
            ErrorMessage(self, "%s is not a valid gradient file." % e.String)
        
