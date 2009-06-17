#Render Dialog Script for Fr0st
#(Re)Started by Brad on April 6th at 8:00 pm.
#Designed to be a basic dialog that will render the current flame to an image file.
#Changelog:
#   Started April 6th.
#   Basic Operations completed April 10th -
#     Currently supports PNG and JPG images, will support more.

import wx, os
from lib.fr0stlib import Flame
from lib.gui import rendering
from lib.pyflam3 import Genome
from _events import EVT_THREAD_MESSAGE, ThreadMessageEvent
from decorators import *

class renderDialog(wx.Dialog):

    def __init__(self, parent, id):
        #Accessible elements:
        #self.Format - The format as determined by the filename -
        #ex. test.png - self.Format='png'
        #self.Destination - output destination for image file
        #self.Width - width of image file
        #self.Height - Height of image file
        #self.Quality - quality of flame file
	self.parent = parent
	
	wx.Dialog.__init__(self, parent, id,
                           title="Render Flame to Image File",
                           size=(400,210))#TODO:Change title to say name 
					  #of current flame - self.parent.flame.name
             
        #Destination Box
        wx.StaticBox(self, 1,"Destination:", pos=(5, 5),size=(390,55)) 
        wx.StaticText(self, 1, "Output Destination:",pos=(10,20))
        self.txtDestination = wx.TextCtrl(self, 1, '',pos=(10,35),size=(280,22))
        wx.Button(self, 3, ". . .", pos=(300,35),size=(75,22))

        #Size Box
        wx.StaticBox(self, 2, "Size:", pos=(5,60),size=(180,75))
        wx.StaticText(self, 2, "Width:", pos=(10,75))
        wx.StaticText(self, 2, "Height:", pos=(10,110))
        self.Width = wx.ComboBox(self, 2, '', pos=(50,70), size=(130,22),
                                 choices=('320','640','1024','1280','2048'))
        self.Height = wx.ComboBox(self, 2, '', pos=(50,105), size=(130,22),
                                  choices=('240','480','768','1024','1536'))
        #Initialize the Values
        self.Width.SetValue("1024")
        self.Height.SetValue("768")
        
        #Quality Box
        wx.StaticBox(self, 3, "Render Options:", pos=(200,60),size=(195,75))
        wx.StaticText(self, 3, "Quality:", pos=(207,80))
        wx.StaticText(self, 3, "Estimator:", pos=(207,110))
        self.Quality = wx.SpinCtrl(self, 3, '', pos=(250,75),size=(140,22))
        self.Quality.SetRange(1,150000)
        self.Estimator = wx.TextCtrl(self, 3, '', pos=(260,105), size=(130,22))
        self.Estimator.SetValue('9')
        #TODO - Add more options. Oversample, etc.
        
        wx.Button(self, 1, "Begin Render", pos=(10,150))
        wx.Button(self, 2, "Close", pos=(300,150))

        
        self.Bind(wx.EVT_BUTTON, self.closeDialog, id=2)
        self.Bind(wx.EVT_BUTTON, self.beginRender, id=1)
        self.Bind(wx.EVT_BUTTON, self.chooseOutputFile, id=3)
        
        self.Centre()
        self.ShowModal()
        self.Destroy()

    def chooseOutputFile(self, event):
        filters = 'All files (*.*)|*.*|PNG File (*.png)|*.png|JPG File (*.jpg)|*.jpg'
        dlg=wx.FileDialog(self, "Choose the Output File", os.getcwd(),
                          "", filters, wx.SAVE)
        if dlg.ShowModal()==wx.ID_OK:
            path = dlg.GetPath()
            self.txtDestination.SetValue(path)         
        dlg.Destroy()
    def closeDialog(self, event):
        self.Close()
    
    def beginRender(self, event):
        #Put in rendering processes here.

        destination = str(self.txtDestination.GetValue())
	#GetValue() returns unicode, change to string
	type = destination[-3:len(destination)+1] #get last 3 characters - filetype
        sizeMatrix = [int(self.Width.GetValue()),int(self.Height.GetValue())]
	#GetValue() returns unicode, change to int
	
	#flame = Genome.from_file('snowflake.flam3')
	intflame = self.parent.flame
	#or maybe Genome.from_string(self.parent.flame)?
	
	self.utype = type.upper()#convert to uppercase for weird names
	if self.utype == 'PNG': self.wxFormat = wx.BITMAP_TYPE_PNG
        elif self.utype == 'JPG': self.wxFormat = wx.BITMAP_TYPE_JPG
	elif self.utype == 'BMP': self.wxFormat = wx.BITMAP_TYPE_BMP
	elif self.utype == 'GIF': self.wxFormat = wx.BITMAP_TYPE_GIF
	elif self.utype == 'PNM': self.wxFormat = wx.BITMAP_TYPE_PNM
	elif self.utype == 'XPM': self.wxFormat = wx.BITMAP_TYPE_XPM
	elif self.utype == 'TIF': self.wxFormat = wx.BITMAP_TYPE_TIF
        #else display format not supported

	#intFlame = self.parent.flame #intermediary flame
	flame = Flame.to_string(intflame)
        
	req = self.parent.renderer.RenderRequest
	#image = wx.ImageFromBuffer(sizeMatrix[0],sizeMatrix[1],
                                   #req(flame,sizeMatrix,self.Quality.GetValue(),int(self.Estimator.GetValue()),progress_func=self.prog))
	req(self.save,sizeMatrix,flame,sizeMatrix,self.Quality.GetValue(),
            int(self.Estimator.GetValue()),filter=.2,progress_func=self.prog)
	print 'render done'
	
	#image.SaveFile(destination, self.wxFormat)
        #wx.Image.SaveFile(self.Destination,self.Format.upper(),wx.BitmapFromBuffer)
        #img.save(self.Destination, self.Format.upper())
    def msgNotImplemented(self,event):
        dlg=wx.MessageDialog(self, "This feature is currently not implemented, but is coming soon",
                         "Not Implemented", wx.OK|wx.ICON_INFORMATION)
        #NOTE: dialog must be initialized to variable to allow for destroy call.
        dlg.ShowModal()
        dlg.Destroy()
        
    def prog(self, py_object, fraction, stage, eta):
	print 'rendering: %.2f%% ETA: %.0f seconds' % (fraction,eta)
	return

    def save(self, size, output_buffer):
        w,h= size
	image = wx.ImageFromBuffer(w, h, output_buffer)
	destination = str(self.txtDestination.GetValue())
	image.SaveFile(destination, self.wxFormat)


