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
import wx
from threading import Event

myEVT_THREAD_MESSAGE = wx.NewEventType()
EVT_THREAD_MESSAGE = wx.PyEventBinder(myEVT_THREAD_MESSAGE, 1)
class ThreadMessageEvent(wx.PyCommandEvent):
    """Notifies the main thread to update something controlled by wx, which is
    not thread-safe.

    Optionally carries arbitrary information accessible through GetArgs().

    Should be used with an id if the receiving widget has more than 1 handler,
    to make sure it goes to the correct one."""
    
    def __init__(self, id=wx.ID_ANY, *args):
        wx.PyCommandEvent.__init__(self, myEVT_THREAD_MESSAGE, id)
        self.Args = args

    def GetArgs(self):
        return self.Args

    # For compatibility with existing code
    GetValue = GetMessage = GetArgs


def InMain(f):
    res = [None]
    bound = Event()
    flag = Event()
    ID = wx.NewId()
    def callback(e):
        self, a, k = e.Args
        try:
            res[0] = f(self, *a, **k)
        except Exception as e:
            res[0] = e
        flag.set()
    def inner(self, *a, **k):
        if not bound.is_set():
            wx.GetApp().Bind(EVT_THREAD_MESSAGE, callback, id=ID)
            bound.set()
        flag.clear()
        wx.PostEvent(self, ThreadMessageEvent(ID, self, a, k))
        flag.wait()
        result, res[0] = res[0], None
        if isinstance(result, Exception):
            raise result
        return result
    return inner
