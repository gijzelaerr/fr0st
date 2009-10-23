from __future__ import with_statement
from threading import Thread, Lock, currentThread
from functools import wraps

try:
    from fr0stlib.threadinterrupt import ThreadInterrupt
except ImportError:
    class ThreadInterrupt(BaseException): pass
    raise ImportWarning("Couldn't import required exception.")

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
            for evt, a, k in f.__bound:
                if type(evt) is tuple:
                    for e in evt:
                        self.Bind(e, f, *a, **k)
                else:
                    self.Bind(evt, f, *a, **k)
    return wrapper


def Catches(exctype):
    """ Makes a function swallow a given exception type and return None
    silently.
    Exctype can be a single exception type or a tuple."""
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


def Locked(lock=None, blocking=True):
    """ Wraps the function in a lock to make sure no more than one thread is
    executing inside it at any given time.

    The blocking flag is passd on to the underlying lock, so it will
    behave as documented in the threading module."""
    if lock is None:
        lock = Lock()
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwds):
            if not lock.acquire(blocking):
                return
            try:
                result = f(*args, **kwds)
            finally:
                lock.release()
            return result
        return wrapper
    return decorator


def Threaded(f):
    """ Splits off a different thread each time the wrapped function is called.
    The thread's name is set to that of the function."""
    @wraps(f)
    def wrapper(*args,**kwds):
        thr = Thread(target=Catches(ThreadInterrupt)(f),
                     args=args, kwargs=kwds, name=f.__name__)
        thr.daemon = True
        thr.start()
    return wrapper


def CallableFrom(name):
    """ Only a thread having the given name will be able to call this function.
    Used for defensive programming, to make sure thread boundaries aren't
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

