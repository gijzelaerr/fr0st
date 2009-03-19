import re

class ItemData(list):
    re_name = re.compile(r'(?<= name=").*?(?=")') # This re is duplicated!
    def __init__(self,string):
        self.append(string)
        self.redo = []
        self.name = None
        
    def TempSave(self,string):
        self.append(string)

    def GetSaveString(self):
        if self.name is None:
            return self[-1]
        return self.re_name.sub(self.name,self[-1])

    def HasChanged(self):
        return self.undo or self.name
    
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
        
