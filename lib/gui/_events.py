import wx


myEVT_IMAGE_READY = wx.NewEventType()
EVT_IMAGE_READY = wx.PyEventBinder(myEVT_IMAGE_READY, 1)
class ImageReadyEvent(wx.PyCommandEvent):
    def __init__(self,*args):
        wx.PyCommandEvent.__init__(self, myEVT_IMAGE_READY, wx.ID_ANY)
        self._data = args

    def GetValue(self):
        return self._data


myEVT_PRINT = wx.NewEventType()
EVT_PRINT = wx.PyEventBinder(myEVT_PRINT, 1)
class PrintEvent(wx.PyCommandEvent):
    def __init__(self,message):
        wx.PyCommandEvent.__init__(self, myEVT_PRINT, wx.ID_ANY)
        self._message = message
        
    def GetValue(self):
        return self._message


myEVT_CANVAS_REFRESH = wx.NewEventType()
EVT_CANVAS_REFRESH = wx.PyEventBinder(myEVT_CANVAS_REFRESH, 1)
class CanvasRefreshEvent(wx.PyCommandEvent):
    def __init__(self,*args):
       wx.PyCommandEvent.__init__(self, myEVT_CANVAS_REFRESH, wx.ID_ANY)
       self._args = args

    def GetValue(self):
        return self._args
