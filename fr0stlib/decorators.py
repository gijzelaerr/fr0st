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
    """ Wraps the function in a lock.

    No more than one thread can execute the function at a time. The blocking
    flag is passed on to the underlying lock, so it will behave as documented
    in the threading module."""
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
    f = Catches(ThreadInterrupt)(f)
    @wraps(f)
    def wrapper(*args,**kwds):
        thr = Thread(target=f, args=args, kwargs=kwds, name=f.__name__)
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

