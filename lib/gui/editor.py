from __future__ import with_statement
import wx, os, sys, re
from wx import stc, PyDeadObjectError

from StyledTextCtrl_2 import PythonSTC
from decorators import *
from toolbar import CreateEditorToolBar
from constants import ID
from _events import EVT_PRINT, PrintEvent


class EditorFrame(wx.Frame):
    
    @BindEvents    
    def __init__(self,parent,id):
        self.title = "Script Editor"
        self.parent = parent
        wx.Frame.__init__(self,parent,wx.ID_ANY, self.title)
 
        self.editor = CodeEditor(self)
        self.log = MyLog(self)

        CreateEditorToolBar(self)
        self.SetSize((865,500))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.editor,1,wx.EXPAND)
        sizer.Add(self.log,0,wx.EXPAND)
        self.SetSizer(sizer)
        self.SetAutoLayout(1)
##        sizer.Fit(self)

        self.wildcard = "Python source (*.py;*.pyw)|*.py;*.pyw|" \
                        "All files (*.*)|*.*"

        # Set up paths
        self.scriptpath = os.path.join(sys.path[0],"scripts", "default.py")


        # Load the default script
        with open(self.scriptpath) as f:
            self.editor.SetValue(f.read())
            
        self.Show(False) # allows running scripts without showing this frame


    @Bind(wx.EVT_CLOSE)
    def OnExit(self,e):

        # Removed this line, script should only be stopped if it has changed.
##        self.parent.OnStopScript()
        
        if self.CheckForChanges() == wx.ID_CANCEL:
            return
        self.Show(False)


    @Bind(wx.EVT_TOOL,id=ID.TBNEW)
    def OnScriptNew(self,e):
        if self.CheckForChanges() == wx.ID_CANCEL:
            return
        self.editor.SetValue("")


    @Bind(wx.EVT_TOOL,id=ID.TBOPEN)    
    def OnScriptOpen(self,e):
        if self.CheckForChanges() == wx.ID_CANCEL:
            return
        self.OpenScript()


    @Bind(wx.EVT_TOOL,id=ID.TBSAVE)
    def OnScriptSave(self,e):
        dDir,dFile = os.path.split(self.scriptpath)
        dlg = wx.FileDialog(self, message="Save file as ...",
                            defaultDir=dDir, 
                            defaultFile=dFile,
                            wildcard=self.wildcard, style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.scriptpath = path = dlg.GetPath()
            if os.path.exists(path):
                dlg2 = wx.MessageDialog(self, '%s already exists.\nDo You want to replace it?'
                                       %path,'Fr0st',wx.YES_NO)
                if dlg2.ShowModal() == wx.ID_NO: return
                dlg2.Destroy()      
            self.SaveScript()
        dlg.Destroy()


    def CheckForChanges(self):
        f = open(self.scriptpath)
        if self.editor.GetText() != f.read():
            self.parent.OnStopScript()
            self.SetFocus() # So the user sees where the dialog comes from.
            dlg = wx.MessageDialog(self, 'Save changes to %s?'
                                   % os.path.split(self.scriptpath)[-1],
                                   'Fr0st',wx.YES_NO|wx.CANCEL)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                self.SaveScript()
            elif result == wx.ID_NO:
                # Reset the script to the saved version, so that it looks like
                # the editor was closed.
                with open(self.scriptpath) as f:
                    self.editor.SetValue(f.read())
            dlg.Destroy()
            return result

    def OpenScript(self):
        dDir,dFile = os.path.split(self.scriptpath)
        dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=dDir,
            defaultFile=dFile, wildcard=self.wildcard, style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.scriptpath = dlg.GetPath()
            with open(self.scriptpath) as f:
                self.editor.SetValue(f.read())
        dlg.Destroy()
        self.SetTitle("Script Editor - %s" % self.scriptpath)
        

    def SaveScript(self):
        with open(self.scriptpath,"w") as f:
            f.write(self.editor.GetText())        





class MyLog(wx.TextCtrl):
    re_exc = re.compile(r'^.*?(?=  File "<string>")',re.DOTALL)
    re_line = re.compile(r'(Script, line \d*, in .*?)$',re.MULTILINE)
    re_linenum = re.compile(r'(?<=Script, line )\d*(?=,)')
    _script = None # This is set by the parent

    @BindEvents
    def __init__(self,parent):
        self.parent = parent
        wx.TextCtrl.__init__(self,parent,-1,
                             style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        self.SetMinSize((264,0))
        self.SetFont(wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL))
        self.oldstderr = sys.stderr   # For debugging purposes!
        sys.stdout = self
        sys.stderr = self
##        self._suppress = 0
##        self._syntax  = 0

    @Catches(PyDeadObjectError)
    def write(self,message):
        """Notifies the main thread to print a message."""
        wx.PostEvent(self,PrintEvent(message))

    @Catches(PyDeadObjectError)
    def _write(self,message):
        self.oldstderr.write("[%s]" %message) # For debugging purposes!

        if not message.startswith("Exception"):
            self.AppendText(message)
            return
        
        message = self.re_exc.sub('',message)
        message = message.replace('File "<string>"','Script')
        lines = (self._script[int(i)-1].strip()
                 for i in self.re_linenum.findall(message))
        message = self.re_line.sub('\g<1>\n    %s',message) %tuple(lines)
        self.AppendText(message)


    @Bind(EVT_PRINT)
    def OnPrint(self,e):
        self._write(e.GetValue())

    if "win32" in sys.platform:
        write = _write
        
     
        # This is the old procedural write method, it's kept here because it
        # works even if write is fed the traceback little pieces at a time.
##    def write(self,message):
##
##        # Prints the script traceback
##        if message.startswith('  File "<string>"'): 
##            self._suppress = 0
##            lines = message.split(",")
##            line  = int(lines[1][6:])
##            message = "  Script, line %d,%s    %s\n"\
##                      %(line,lines[2],self._script[line-1].strip())
##                      
##        # suppresses the internal fr0st tracebacks (each generates 3 writes)
##        elif message.startswith('  File "'): 
##             self._suppress = 3
##        
##        # Handles syntax errors passed to write() as single tokens, not lines.
##        elif message == '", line ':
##            self._syntax  = 1      
##        elif self._syntax:
##            self._syntax  = 0
##            self._suppress = 0
##            message = '  Script, line %s ' %message
##            
##        # Didn't trigger anything, so we just decrease the suppress count.
##        elif self._suppress:
##            self._suppress -= 1
##
##        # Finally, print the message
##        if not self._suppress:
##            self.tc.AppendText(message)    


    # Just a stub to test TreeCtrl
    WriteText = write


class CodeEditor(PythonSTC):
    def __init__(self, parent):
        PythonSTC.__init__(self, parent, -1)
        self.SetUpEditor()

    # Some methods to make it compatible with how the wxTextCtrl is used
    def SetValue(self, value):
        if wx.USE_UNICODE:
            value = value.decode('iso8859_1')
        val = self.GetReadOnly()
        self.SetReadOnly(False)
        self.SetText(value)
        self.EmptyUndoBuffer()
        self.SetSavePoint()
        self.SetReadOnly(val)

    def SetEditable(self, val):
        self.SetReadOnly(not val)

    def IsModified(self):
        return self.GetModify()

    def Clear(self):
        self.ClearAll()

    def SetInsertionPoint(self, pos):
        self.SetCurrentPos(pos)
        self.SetAnchor(pos)

    def ShowPosition(self, pos):
        line = self.LineFromPosition(pos)
        #self.EnsureVisible(line)
        self.GotoLine(line)

    def GetLastPosition(self):
        return self.GetLength()

    def GetPositionFromLine(self, line):
        return self.PositionFromLine(line)

    def GetRange(self, start, end):
        return self.GetTextRange(start, end)

    def GetSelection(self):
        return self.GetAnchor(), self.GetCurrentPos()

    def SetSelection(self, start, end):
        self.SetSelectionStart(start)
        self.SetSelectionEnd(end)

    def SelectLine(self, line):
        start = self.PositionFromLine(line)
        end = self.GetLineEndPosition(line)
        self.SetSelection(start, end)
        
    def SetUpEditor(self):
        """
        This method carries out the work of setting up the demo editor.            
        It's seperate so as not to clutter up the init code.
        """
        import keyword
        
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))

        # Enable folding
        self.SetProperty("fold", "1" ) 

        # Highlight tab/space mixing (shouldn't be any)
        self.SetProperty("tab.timmy.whinge.level", "1")

        # Set left and right margins
        self.SetMargins(2,2)

        # Set up the numbers in the margin for margin #1
        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        # Reasonable value for, say, 4-5 digits using a mono font (40 pix)
        self.SetMarginWidth(1, 40)

        # Indentation and tab stuff
        self.SetIndent(4)               # Proscribed indent size for wx
        self.SetIndentationGuides(True) # Show indent guides
        self.SetBackSpaceUnIndents(True)# Backspace unindents rather than delete 1 space
        self.SetTabIndents(True)        # Tab key indents
        self.SetTabWidth(4)             # Proscribed tab size for wx
        self.SetUseTabs(False)          # Use spaces rather than tabs, or
                                        # TabTimmy will complain!    
        # White space
        self.SetViewWhiteSpace(False)   # Don't view white space

        # EOL: Since we are loading/saving ourselves, and the
        # strings will always have \n's in them, set the STC to
        # edit them that way.            
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        self.SetViewEOL(False)
        
        # No right-edge mode indicator
        self.SetEdgeMode(stc.STC_EDGE_NONE)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        # and now set up the fold markers
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,  "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,  "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,    "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,  "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS, "white", "black")

        # Global default style
        if wx.Platform == '__WXMSW__':
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 
                              'fore:#000000,back:#FFFFFF,face:Courier New')
        elif wx.Platform == '__WXMAC__':
            # TODO: if this looks fine on Linux too, remove the Mac-specific case 
            # and use this whenever OS != MSW.
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 
                              'fore:#000000,back:#FFFFFF,face:Monaco')
        else:
            defsize = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT).GetPointSize()
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 
                              'fore:#000000,back:#FFFFFF,face:Courier,size:%d'%defsize)

        # Clear styles and revert to default.
        self.StyleClearAll()

        # Following style specs only indicate differences from default.
        # The rest remains unchanged.

        # Line numbers in margin
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,'fore:#000000,back:#99A9C2')    
        # Highlighted brace
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT,'fore:#00009D,back:#FFFF00')
        # Unmatched brace
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD,'fore:#00009D,back:#FF0000')
        # Indentation guide
        self.StyleSetSpec(wx.stc.STC_STYLE_INDENTGUIDE, "fore:#CDCDCD")

        # Python styles
        self.StyleSetSpec(wx.stc.STC_P_DEFAULT, 'fore:#000000')
        # Comments
        self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE,  'fore:#008000,back:#F0FFF0')
        self.StyleSetSpec(wx.stc.STC_P_COMMENTBLOCK, 'fore:#008000,back:#F0FFF0')
        # Numbers
        self.StyleSetSpec(wx.stc.STC_P_NUMBER, 'fore:#008080')
        # Strings and characters
        self.StyleSetSpec(wx.stc.STC_P_STRING, 'fore:#800080')
        self.StyleSetSpec(wx.stc.STC_P_CHARACTER, 'fore:#800080')
        # Keywords
        self.StyleSetSpec(wx.stc.STC_P_WORD, 'fore:#000080,bold')
        # Triple quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLE, 'fore:#800080,back:#FFFFEA')
        self.StyleSetSpec(wx.stc.STC_P_TRIPLEDOUBLE, 'fore:#800080,back:#FFFFEA')
        # Class names
        self.StyleSetSpec(wx.stc.STC_P_CLASSNAME, 'fore:#0000FF,bold')
        # Function names
        self.StyleSetSpec(wx.stc.STC_P_DEFNAME, 'fore:#008080,bold')
        # Operators
        self.StyleSetSpec(wx.stc.STC_P_OPERATOR, 'fore:#800000,bold')
        # Identifiers. I leave this as not bold because everything seems
        # to be an identifier if it doesn't match the above criterae
        self.StyleSetSpec(wx.stc.STC_P_IDENTIFIER, 'fore:#000000')

        # Caret color
        self.SetCaretForeground("BLUE")
        # Selection background
        self.SetSelBackground(1, '#66CCFF')

        self.SetSelBackground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self.SetSelForeground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

    def RegisterModifiedEvent(self, eventHandler):
        self.Bind(wx.stc.EVT_STC_CHANGE, eventHandler)


