import re, os
        
    
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
            self.redo.extend(self[1:])
            self[:] = self[:1]
            self._name = self.re_name.findall(self[-1])[0]
            return self[-1]
        

    def Redo(self):
        if self.redo:
            list.append(self,self.redo.pop())
            self._name = self.re_name.findall(self[-1])[0]
            return self[-1]


    def _get_undo(self):
        return len(self) - 1

    undo = property(_get_undo)


    def _get_name(self):
        return ('* ' if self.undo else '') + self._name

    def _set_name(self,v):
        self.append(self.re_name.sub(v, self[-1]))
        self._name = v[1:] if v[:2] == '* ' else v

    name = property(_get_name, _set_name)

