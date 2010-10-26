import os, re, wx, numpy, itertools
import xml.etree.cElementTree as etree
import wx.combo
from  wx.lib.filebrowsebutton import FileBrowseButton

from fr0stlib import Palette, load_flamestrings, hsv2rgb, rgb2hsv
from fr0stlib.gui.utils import Box, ErrorMessage
from fr0stlib.gui.config import config

# support for ugr palettes - thx bobby
_ugr_main_re = re.compile(
        '\s*(.*?)\s*{\s*gradient:\s*title="(.*?)"\s*smooth=(yes|no)\s*(.*?)\}', 
        re.DOTALL)

_ugr_inner_re = re.compile('\s*index=(\d+)\s*color=(\d+)')

def _load_ugr_iter(filename):
    with open(filename) as  gradient_fd:
        text = gradient_fd.read()

    index_ratio = 255.0 / 399.0

    newpal = numpy.arange(0,256)
    
    for match in _ugr_main_re.finditer(text):
        item_name, title, smooth, inner = match.groups()

        indices = numpy.array([[0,0,0,0]])

        for index, color in _ugr_inner_re.findall(inner):
            # -401 being a legal index is just stupid...
            index = float(index)
            while index < 0:
                index += 400

            color = int(color)
    
            r = (color & 0xFF0000) >> 16
            g = (color & 0xFF00) >> 8
            b = (color & 0xFF)

            hsv = rgb2hsv((r, g, b))

            indices = numpy.append(indices,[[index,hsv[0],hsv[1],hsv[2]]],0)
   
        # pad the vectors before and after
        # starter element was already there
        indices[0,:] = indices[-1,:]
        indices[0,0] -= 400
        # add last element
        indices = numpy.append(indices,[indices[1,:]],0)
        indices[-1,0] += 400

        # normalize all indices to 0-1
        indices[:,0] *= index_ratio

        # make sure consecutive hues do not change by > 0.5
        for idx in range(numpy.size(indices,0)-1):
            if indices[idx+1,1]-indices[idx,1] > 0.5:
                indices[idx+1,1] -= 0.5
            elif indices[idx,1]-indices[idx+1,1] > 0.5:
                indices[idx+1,1] += 0.5

        # interpolate each color separately
        newh = numpy.interp(newpal,indices[:,0],indices[:,1])
        news = numpy.interp(newpal,indices[:,0],indices[:,2])
        newv = numpy.interp(newpal,indices[:,0],indices[:,3])

        # now we have 256 elements in each h,s,v
        palette = Palette()
        palette[:] = map(hsv2rgb, itertools.izip(newh,news,newv))

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
        elif ext == ".map":
            with open(path,'r') as mf:
                lns = mf.readlines()
            # Each string in the list contains three ints
            # but possibly other stuff, so just take the first
            # three values
            data = [map(float, s.split()[0:3]) for s in lns]
            if len(data) != 256:
                raise ParsingError('Wrong number of palette entries specified: '
                                   '%s != %s' % (256, len(lst)))
            p = Palette()
            p.data[:] = data
            return ((os.path.splitext(os.path.basename(path))[0], p),)
        elif ext == ".ugr":
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
        
