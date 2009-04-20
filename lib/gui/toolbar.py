import wx
from constants import ID

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
    
    tb.AddSimpleTool(ID.TBNEW, GetBMP(wx.ART_NEW),
                     "New", "New flame file")

    tb.AddSimpleTool(ID.TBNEW2, GetBMP(wx.ART_NEW),
                     "New", "New flame")

    tb.AddSimpleTool(ID.TBOPEN, GetBMP(wx.ART_FILE_OPEN),
                     "Open", "Open a flame file")

    tb.AddSimpleTool(ID.TBSAVE, GetBMP(wx.ART_FLOPPY),
                     "Save", "Save the current flame")

    tb.AddSeparator()

    tb.AddSimpleTool(ID.UNDO, GetBMP(wx.ART_UNDO),
                     "Undo", "Undo the last change on the curently selected flame.")
    tb.EnableTool(ID.UNDO,False)
    
    tb.AddSimpleTool(ID.REDO, GetBMP(wx.ART_REDO),
                     "Redo", "Redo the last change on the curently selected flame.")
    tb.EnableTool(ID.REDO,False)
    
    tb.AddSeparator()
    
    tb.AddSimpleTool(ID.TBOPENSCRIPT, GetBMP(wx.ART_FILE_OPEN),
                     "Open Script", "")

    tb.AddSimpleTool(ID.TBRUN, GetBMP(wx.ART_EXECUTABLE_FILE),
                     "Run Script", "Run the currently loaded script file")
    
    tb.AddSimpleTool(ID.TBSTOP, GetBMP(wx.ART_ERROR),
                     "Stop Script", "Stop script execution")

    tb.AddSimpleTool(ID.TBEDITOR, GetBMP(wx.ART_MISSING_IMAGE),
                     "Editor", "Open the script editor")
    
    tb.Realize()



def CreateEditorToolBar(parent):

    TBFLAGS = ( wx.TB_HORIZONTAL
                | wx.TB_FLAT
                )

    tb = parent.CreateToolBar(TBFLAGS)
    
    tb.AddSimpleTool(ID.TBNEW, GetBMP(wx.ART_NEW),
                     "New", "Long help for 'New'")

    tb.AddSimpleTool(ID.TBOPEN, GetBMP(wx.ART_FILE_OPEN),
                     "Open", "Long help for 'Open'")

    tb.AddSimpleTool(ID.TBSAVE, GetBMP(wx.ART_FLOPPY),
                     "Save", "Long help for 'Save'")

    tb.AddSeparator()

    tb.AddSimpleTool(ID.TBRUN, GetBMP(wx.ART_EXECUTABLE_FILE),
                     "Run Script", "Run the currently loaded script file")
    
    tb.AddSimpleTool(ID.TBSTOP, GetBMP(wx.ART_ERROR),
                     "Stop Script", "Stop script execution")

    
    tb.Realize()
    