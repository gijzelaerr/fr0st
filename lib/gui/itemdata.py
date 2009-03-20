import re, os
from collections import defaultdict

from lib import functions

class ItemData(list):
    re_name = re.compile(r'(?<= name=").*?(?=")') # This re is duplicated!
    _changes = defaultdict(dict)
    _all = []
    
    def __init__(self,string):
        self.append(string)
        self.redo = []
        self.name = None
        self._all.append(self)
        self._index = len(self._all)
        
##    def TempSave(self, flame, path):
##        string = flame.to_string()
##        self.append(string)
####        self._changes[path][flame.name] = string
####        new_path = os.path.splitext(path)[0] + ".temp"
####        functions.save_flames(new_path,*self._changes[path].values())

    def GetSaveString(self):
        if self.name is not None:
            self[-1] = self.re_name.sub(self.name,self[-1])
        return self[-1]

    def HasChanged(self):
        return self.undo or self.name

    def Reset(self):
        self[:] = self[-1:]
        self.redo = []
        self.name = None
    
    def Undo(self):
        if self.undo:
            self.redo.append(self.pop())
            return self[-1]

    def Redo(self):
        if seld.redo:
            self.append(self.redo.pop())
            return self[-1]

    def _get_undo(self):
        return len(self) - 1

    undo = property(_get_undo)
        
