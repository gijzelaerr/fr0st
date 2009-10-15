import ctypes, inspect, threading, sys


class ThreadInterrupt(BaseException): pass


def interrupt(thread, exctype=ThreadInterrupt):
    """Raises an exception in a thread"""

    if float(sys.version[:3]) >= 2.6:
        ident = thread.ident
    else: # Do it the old way...
        for tid, tobj in threading._active.items():
            if tobj is thread:
                ident = tid
                break
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ident,ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def interruptall(name=None,exctype=ThreadInterrupt):
    """Interrupts all threads other than the caller which share the given name.
    If no name is given, all threads other than the caller are interrupted."""
        
    for thread in threading.enumerate():
        # use thread.name once support for 2.5 is dropped
        if name and thread.getName() != name: continue        
        if thread is threading.currentThread(): continue
##        if not thread.is_alive(): continue
        interrupt(thread, exctype)
