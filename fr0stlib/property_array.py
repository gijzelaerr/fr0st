import collections, sys

import numpy as N


class _property_array(N.ndarray):
    def __new__(cls, parent, instance, data):
        obj = N.asarray(data).view(cls)
        def callback():
            print "callback called"
            parent.fset(instance, obj)
        obj.callback = callback
        return obj


    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.callback = getattr(obj, "callback", None)


    def __setitem__(self, pos, val):
        N.ndarray.__setitem__(self, pos, val)
        self.callback()
    

    

class property_array(property): 
    def __init__(self, fget, fset=None, fdel=None, fdoc=None):
        if fdel is not None or fdoc is not None:
            raise ValueError("fdel and fdoc are not supported")
        
        def _fget(instance):
            return _property_array(self, instance, fget(instance))
        
        property.__init__(self, _fget, fset)
