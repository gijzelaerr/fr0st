#!/usr/bin/env python
import wx, os, sys

os.chdir(sys.path[0])

from lib.gui import Fr0stApp


if __name__ == '__main__':
    app = Fr0stApp()
    app.MainLoop()
