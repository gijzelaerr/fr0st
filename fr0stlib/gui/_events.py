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
import wx, time

myEVT_THREAD_MESSAGE = wx.NewEventType()
EVT_THREAD_MESSAGE = wx.PyEventBinder(myEVT_THREAD_MESSAGE, 1)
class ThreadMessageEvent(wx.PyCommandEvent):
    """Used to send information to a callback function in the main thread.

    Should have an id if the receiving widget has more than 1 handler. Can
    carry arbitrary information accessible through e.Args."""
    def __init__(self, id=wx.ID_ANY, *args):
        wx.PyCommandEvent.__init__(self, myEVT_THREAD_MESSAGE, id)
        self.Args = args


# Specify id to make sure this event doesn't interfere with anything else
__ID = wx.NewId()

def InMainSetup(__init__):
    def inner(self, *a, **k):
        __init__(self, *a, **k)
        def callback(e):
            res, f, a, k = e.Args
            try:
                res.append(f(*a, **k))
            except Exception as e:
                res.append(e)
        self.Bind(EVT_THREAD_MESSAGE, callback, id=__ID)
    return inner


def InMain(f):
    """Decorator that forces functions to be executed in the main thread.

    The thread in which the function is called waits on the result, so the code
    can be reasoned about as if it was single-threaded."""
    def inner(*a, **k):
        res = []
        wx.PostEvent(wx.GetApp(), ThreadMessageEvent(__ID, res, f, a, k))
        while not res:
            time.sleep(.0001)
        result = res[0]
        if isinstance(result, Exception):
            raise result
        return result
    return inner
