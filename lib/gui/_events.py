import wx


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
        self._args = args

    def GetArgs(self):
        return self._args

    # For compatibility with existing code
    GetValue = GetMessage = GetArgs
