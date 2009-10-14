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
    def callback(e):
        flag, self, a, k = e.Args
        try:
            res[0] = f(self, *a, **k)
        except Exception as e:
            res[0] = e
        flag.set()
    bound = Event()
    ID = wx.NewId()
    def inner(self, *a, **k):
        if not bound.is_set():
            wx.GetApp().Bind(EVT_THREAD_MESSAGE, callback, id=ID)
            bound.set()
        flag = Event()
        wx.PostEvent(self, ThreadMessageEvent(ID, flag, self, a, k))
        flag.wait()
        result = res[0]
        res[0] = None
        if isinstance(result, Exception):
            raise result
        return result
    return inner
