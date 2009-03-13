from __future__ import with_statement
from threading import Thread, Lock
from functools import wraps

from lib._exceptions import *

def Bind(event,*args,**kwds):
    def bind(f):
        f._bound = getattr(f,"_bound",[]) + [(event,args,kwds)]
        return f
    return bind


def BindEvents(__init__):
    @wraps(__init__)
    def wrapper(self,*args,**kwds):
        __init__(self,*args,**kwds)
        for name in self.__class__.__dict__:
            f = getattr(self,name)
            if not hasattr(f,"_bound"): continue
            for evt,args, kwargs in f._bound:
                self.Bind(evt, f, *args, **kwargs)
    return wrapper


def Catches(exctype):
    def catches(f):
        @wraps(f)
        def wrapper(*args,**kwds):
            try:
                result = f(*args,**kwds)
            except exctype:
                result = None
            return result
        return wrapper
    return catches


def Locked(f):
    lock = Lock()
    @wraps(f)
    def wrapper(*args,**kwds):
        result = None
        with lock:
            result = f(*args,**kwds)
        return result
    return wrapper


def XLocked(f):
    """A lock that rejects concurrent access, instead of delaying it."""
    lock = Lock()
    @wraps(f)
    def wrapper(*args,**kwds):
        result = None
        if lock.locked(): return
        with lock:
            result = f(*args,**kwds)
        return result
    return wrapper


def Threaded(f):
    def threaded(*args,**kwds):
        Thread(target=Catches(ThreadInterrupt)(f),
               args=args,kwargs=kwds,name=f.__name__).start()
##    return threaded
    return f  # test the gui without threading
