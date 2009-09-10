import wx
from constants import ID
from lib.gui.utils import LoadIcon

def GetBMP(name,client=wx.ART_TOOLBAR,size=(16,16)):
    return wx.ArtProvider.GetBitmap(name, client, size)


def CreateToolBar(parent):
    tb = parent.CreateToolBar(wx.TB_HORIZONTAL |
                              wx.TB_FLAT)
    parent.tb = tb
    add = tb.AddSimpleTool
    
##    add(ID.FNEW, GetBMP(wx.ART_NEW),
##        "New", " New flame file")
    add(ID.FNEW2, GetBMP(wx.ART_NEW),
        "New", " New flame")
    add(ID.FOPEN, GetBMP(wx.ART_FILE_OPEN),
        "Open", " Open a flame file")
    add(ID.FSAVE, GetBMP(wx.ART_FLOPPY),
        "Save", " Save the current flame file.")    
    add(ID.FSAVEAS, GetBMP(wx.ART_FLOPPY),
        "Save as", " Save the current flame file to a different location.")
    tb.AddSeparator()
    add(ID.UNDO, GetBMP(wx.ART_UNDO),
        "Undo", " Undo the last change to the current flame.")    
    add(ID.REDO, GetBMP(wx.ART_REDO),
        "Redo", " Redo the last change to the current flame.")   
    tb.AddSeparator()   
    add(ID.SOPEN, GetBMP(wx.ART_FILE_OPEN),
        "Open Script", "")
    add(ID.RUN, LoadIcon('toolbar', 'Run'),
        "Run Script", " Run the currently loaded script file") 
    add(ID.STOP, GetBMP(wx.ART_ERROR),
        "Stop Script", " Stop script execution")
    add(ID.EDITOR, GetBMP(wx.ART_MISSING_IMAGE),
        "Editor", " Open the script editor")
    tb.AddSeparator()
    add(ID.PREVIEW, GetBMP(wx.ART_MISSING_IMAGE),
        "Preview", " Open the preview frame")
    add(ID.RENDER, GetBMP(wx.ART_EXECUTABLE_FILE),
        "Render", " Render flame to image file")
    
    tb.Realize()


def CreateEditorToolBar(parent):
    tb = parent.CreateToolBar(wx.TB_HORIZONTAL |
                              wx.TB_FLAT)
    parent.tb = tb
    add = tb.AddSimpleTool
 
    add(ID.SNEW, GetBMP(wx.ART_NEW),
        "New", " Long help for 'New'")
    add(ID.SOPEN, GetBMP(wx.ART_FILE_OPEN),
        "Open", " Long help for 'Open'")
    add(ID.SSAVE, GetBMP(wx.ART_FLOPPY),
        "Save", " Long help for 'Save'")
    add(ID.SSAVEAS, GetBMP(wx.ART_FLOPPY),
        "Save as", " Long help for 'Save as'")
    tb.AddSeparator()
    add(ID.RUN, LoadIcon('toolbar', 'Run'),
        "Run Script", " Run currently loaded script.")
    add(ID.STOP, GetBMP(wx.ART_ERROR),
        "Stop Script", " Stop script execution")

    tb.Realize()
