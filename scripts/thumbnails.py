"""
Tumbnail generator - Fr0st sample script

This scripts goes trhough a folder recursively, generating
thumbnails from all flame files it finds, and saving them in a
folder with the same structure.
The name of the file a particular flame comes from is prepended
to the output name.

The default folder is /parameters.
"""

# TODO: Needs to be rewritten using a higher level interface for loading and
# saving flames.


import os, sys
from fr0stlib.gui.renderer import render

basepath = "parameters"

settings = {'size': (128,96),
            'quality': 10,
            'estimator': 0}

def find_flamefiles(top):
    for (dirpath, dirnames, filenames) in os.walk(top):
        for filename in filenames:
            if filename.endswith(".flame"):
                yield os.path.join(dirpath, filename)


for path in find_flamefiles(basepath):
    prefix = os.path.commonprefix((basepath, path))
    partial = path[len(prefix)+1:]
    dest = os.path.join(basepath, "thumbnails", os.path.splitext(partial)[0])
    if not os.path.exists(dest):
        os.makedirs(dest)
    i = 0
    strings = Flame.load_file(path)
    for s in strings:
        output_buffer = render(s, **settings)
        w,h = settings['size']
        image = wx.ImageFromBuffer(w, h, output_buffer)
        image.SaveFile(os.path.join(dest, "%04d.png" %i),
                       wx.BITMAP_TYPE_PNG)
        print i
        i += 1
    
