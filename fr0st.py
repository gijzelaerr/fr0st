#!/usr/bin/env python
import wx, os, sys

#TODO: Not sure what this was for.  Causes problems with 
#TODO: py2exe because sys.path[0] is a zip file.
#os.chdir(sys.path[0])

from fr0stlib.gui import Fr0stApp


if __name__ == '__main__':
    app = Fr0stApp()
    app.MainLoop()
