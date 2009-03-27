import re, os


class ItemData(list):
    re_name = re.compile(r'(?<= name=").*?(?=")') # This re is duplicated!
    
    def __init__(self, name, string):
        self.append(string)
        self.redo = []
        self._name = name
        

    def append(self,v):
        list.append(self,v)
        self.redo = []

        
    def GetSaveString(self):
        return self[-1]


    def HasChanged(self):
        return self.undo #or self.name


    def Reset(self):
        self[:] = self[-1:]
        self.redo = []
##        self.name = None

        
    def Undo(self):
        if self.undo:
            self.redo.append(self.pop())
            return self[-1]


    def Redo(self):
        if self.redo:
            list.append(self,self.redo.pop())
            return self[-1]


    def _get_undo(self):
        return len(self) - 1

    undo = property(_get_undo)


    def _get_name(self):
        return self._name

    def _set_name(self,v):
        self._name = v
        self.append(self.re_name.sub(self._name,self[-1]))

    name = property(_get_name, _set_name)
        
