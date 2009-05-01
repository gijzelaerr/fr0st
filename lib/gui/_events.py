import wx


myEVT_THREAD_MESSAGE = wx.NewEventType()
EVT_THREAD_MESSAGE = wx.PyEventBinder(myEVT_THREAD_MESSAGE, 1)
class ThreadMessageEvent(wx.PyCommandEvent):
    """Notifies the main thread to update something controlled by wx, which is
    not thread-safe.

    This event type can optionally carry arbitrary information which can be
    retrieved through GetMessage().

    Should be used no more than once for each widget, to avoid multiple handlers
    catching an event only meant for one of them."""
    
    def __init__(self,*args):
        wx.PyCommandEvent.__init__(self, myEVT_THREAD_MESSAGE, wx.ID_ANY)
        self._args = args

    def GetMessage(self):
        return self._args

    # For compatibility with existing code
    GetArgs = GetValue = GetMessage
    
