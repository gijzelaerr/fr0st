from __future__ import with_statement
from threading import Thread, Lock, currentThread
from functools import wraps

try:
    from lib._exceptions import ThreadInterrupt
except ImportError:
    raise ImportWarning("Couldn't import required exception.")
    class ThreadInterrupt(BaseException): pass

class ThreadingError(Exception): pass


def Bind(evt, *args, **kwds):
    """ Bind wx events to their respective handlers. Used in conjunction with
    BindEvents."""
    def bind(f):
        f.__bound = getattr(f,"__bound",[]) + [(evt, args, kwds)]
        return f
    return bind


def BindEvents(__init__):
    """ This needs to wrap a given class' __init__ method to enable that class
    to use the Bind decorator."""
    @wraps(__init__)
    def wrapper(self, *args, **kwds):
        __init__(self, *args, **kwds)
        for name in vars(self.__class__):
            f = getattr(self, name)
            if not hasattr(f, "__bound"): continue
            for evt, args, kwds in f.__bound:
                self.Bind(evt, f, *args, **kwds)
    return wrapper


def Catches(exctype):
    """ Makes a function swallow a given exception type and return None
    silently."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args,**kwds):
            try:
                result = f(*args, **kwds)
            except exctype:
                result = None
            return result
        return wrapper
    return decorator


def Locked(blocking=True):
    """ Wraps the function in a lock to make sure no more than one thread is
    executing inside it at any given time.

    The blocking flag is passd on to the underlying lock, so it will
    behave as documented in the threading module."""
    lock = Lock()
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwds):
            if not lock.acquire(blocking):
                return
            result = f(*args, **kwds)
            lock.release()
            return result
        return wrapper
    return decorator


def Threaded(f):
    """ Splits off a different thread each time the wrapped function is called.
    The thread's name is set to that of the function."""
    @wraps(f)
    def wrapper(*args,**kwds):
        Thread(target=Catches(ThreadInterrupt)(f),
               args=args, kwargs=kwds, name=f.__name__).start()
    return wrapper


def CallableFrom(name):
    """ Only a thread having the given name will be able to call this function.
    Used for defensive programming, to making sure thread boundaries aren't
    being violated."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwds):
            if currentThread().getName() != name:
                raise ThreadingError('Function %s may only be called from '
                                     'thread "%s"'
                                     %(f.__name__, name))
            return f(*args, **kwds)
        return wrapper
    return decorator

