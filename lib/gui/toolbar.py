import wx
from constants import ID
from lib.gui.utils import LoadIcon

def GetBMP(name,client=wx.ART_TOOLBAR,size=(16,16)):
    return wx.ArtProvider.GetBitmap(name, client, size)


def CreateToolBar(parent):

    TBFLAGS = ( wx.TB_HORIZONTAL
                #| wx.NO_BORDER
                | wx.TB_FLAT
                #| wx.TB_TEXT
                #| wx.TB_HORZ_LAYOUT
                )

    tb = parent.CreateToolBar(TBFLAGS)
    parent.tb = tb
    
    tb.AddSimpleTool(ID.FNEW, GetBMP(wx.ART_NEW),
                     "New", " New flame file")

    tb.AddSimpleTool(ID.FNEW2, GetBMP(wx.ART_NEW),
                     "New", " New flame")

    tb.AddSimpleTool(ID.FOPEN, GetBMP(wx.ART_FILE_OPEN),
                     "Open", " Open a flame file")

    tb.AddSimpleTool(ID.FSAVE, GetBMP(wx.ART_FLOPPY),
                     "Save", " Save the current flame file.")
    
    tb.AddSimpleTool(ID.FSAVEAS, GetBMP(wx.ART_FLOPPY),
                     "Save as", " Save the current flame file to a different location.")
    
    tb.AddSeparator()

    tb.AddSimpleTool(ID.UNDO, GetBMP(wx.ART_UNDO),
                     "Undo", " Undo the last change to the current flame.")
    
##    tb.AddSimpleTool(ID.UNDOALL, GetBMP(wx.ART_UNDO),
##                     "Undo All", " Revert current flame to saved status.")
    
    tb.AddSimpleTool(ID.REDO, GetBMP(wx.ART_REDO),
                     "Redo", " Redo the last change to the current flame.")
    
    tb.AddSeparator()
    
    tb.AddSimpleTool(ID.SOPEN, GetBMP(wx.ART_FILE_OPEN),
                     "Open Script", "")

    tb.AddSimpleTool(ID.RUN, LoadIcon('toolbar', 'Run'),
                     "Run Script", " Run the currently loaded script file")
    
    tb.AddSimpleTool(ID.STOP, GetBMP(wx.ART_ERROR),
                     "Stop Script", " Stop script execution")

    tb.AddSimpleTool(ID.EDITOR, GetBMP(wx.ART_MISSING_IMAGE),
                     "Editor", " Open the script editor")

    tb.AddSeparator()

    tb.AddSimpleTool(ID.PREVIEW, GetBMP(wx.ART_MISSING_IMAGE),
                     "Preview", " Open the preview frame")

    tb.AddSimpleTool(ID.RENDER, GetBMP(wx.ART_EXECUTABLE_FILE),
                     "Render", " Render flame to image file")
    
    tb.Realize()



def CreateEditorToolBar(parent):

    TBFLAGS = ( wx.TB_HORIZONTAL
                | wx.TB_FLAT
                )

    tb = parent.CreateToolBar(TBFLAGS)
    parent.tb = tb
    
    tb.AddSimpleTool(ID.SNEW, GetBMP(wx.ART_NEW),
                     "New", " Long help for 'New'")

    tb.AddSimpleTool(ID.SOPEN, GetBMP(wx.ART_FILE_OPEN),
                     "Open", " Long help for 'Open'")

    tb.AddSimpleTool(ID.SSAVE, GetBMP(wx.ART_FLOPPY),
                     "Save", " Long help for 'Save'")
    
    tb.AddSimpleTool(ID.SSAVEAS, GetBMP(wx.ART_FLOPPY),
                     "Save as", " Long help for 'Save as'")

    tb.AddSeparator()

    tb.AddSimpleTool(ID.RUN, LoadIcon('toolbar', 'Run'),
                     "Run Script", " Run the currently loaded script file")
    
    tb.AddSimpleTool(ID.STOP, GetBMP(wx.ART_ERROR),
                     "Stop Script", " Stop script execution")

    
    tb.Realize()
    
