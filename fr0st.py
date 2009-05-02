import wx, os, sys

os.chdir(sys.path[0])

from lib.gui import MainWindow


if __name__ == '__main__':
    app = wx.App(0) # 0 makes stderr go to the console. For debugging!
    frame = MainWindow(None, wx.ID_ANY)
    app.MainLoop()
