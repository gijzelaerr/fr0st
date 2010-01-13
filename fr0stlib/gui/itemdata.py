##############################################################################
#  Fractal Fr0st - fr0st
#  https://launchpad.net/fr0st
#
#  Copyright (C) 2009 by Vitor Bosshard <algorias@gmail.com>
#
#  Fractal Fr0st is free software; you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this library; see the file COPYING.LIB.  If not, write to
#  the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 02111-1307, USA.
##############################################################################
import os, re


class ParentData(object):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.name = os.path.basename(path)
        self.imgindex = 0


class ItemData(list):
    re_name = re.compile(r'(?<= name=").*?(?=")')
    
    def __init__(self, string):
        self.append(string)
        self.redo = []
        self._name = (self.re_name.findall(string) or ("Untitled",))[0]
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
