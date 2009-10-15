import re
        
    
class ItemData(list):
    re_name = re.compile(r'(?<= name=").*?(?=")')
    
    def __init__(self, string, name=None):
        self.append(string)
        self.redo = []
        self._name = name or self.re_name.findall(string)[0]
        self.imgindex = -1


    def append(self,v):
        list.append(self,v)
        self.redo = []


    def HasChanged(self):
        return self.undo


    def Reset(self):
        """Deletes the undo and redo lists, leaving the flame intact."""
        self[:] = self[-1:]
        self.redo = []


    def Undo(self):
        if self.undo:
            self.redo.append(self.pop())
            self._name = self.re_name.findall(self[-1])[0]
            return self[-1]


    def UndoAll(self):
        if self.undo:
            self.redo.extend(reversed(self[1:]))
            self[:] = self[:1]
            self._name = self.re_name.findall(self[-1])[0]
            return self[-1]
        

    def Redo(self):
        if self.redo:
            list.append(self,self.redo.pop())
            self._name = self.re_name.findall(self[-1])[0]
            return self[-1]


    def RedoAll(self):
        if self.redo:
            self.extend(reversed(self.redo))
            del self.redo[:]
            self._name = self.re_name.findall(self[-1])[0]
            return self[-1]


    @property
    def undo(self):
        return len(self) - 1


    @property
    def name(self):
        return ('* ' if self.undo else '') + self._name
    @name.setter
    def name(self, v):
        self._name = v[2:] if v[:2] == '* ' else v
        self.append(self.re_name.sub(self._name, self[-1]))
