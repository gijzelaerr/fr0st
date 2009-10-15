import wx
from collections import defaultdict


class ConstantFactory():
    def __init__(self,default):
        self.__dict__["d"] = defaultdict(default)
        
    def __getattr__(self,name):
        return self.d[name]

    def __setattr__(self,name,v):
        raise AttributeError("IDs are read-only")

    def __delattr__(self,name):
        raise AttributeError("IDs are read-only")

ID = ConstantFactory(wx.NewId)


