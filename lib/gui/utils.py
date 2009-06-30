import wx, os


def LoadIcon(*path):
    img = wx.Image(os.path.join('lib','gui','icons',*path) + '.png',
                                type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16,16)
    return wx.BitmapFromImage(img)
