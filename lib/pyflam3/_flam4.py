from ctypes import *

import itertools
import sys


try:
	libflam4 = CDLL('Flam4CUDA_LIB.dll')
except WindowsError:
	# Assume file not found
	import os.path
	# Find the win32_dlls sub directory
	this_dir = os.path.dirname(__file__)
	dll_dir = os.path.join(this_dir, 'win32_dlls')
	# Not add it to the PATH
	sys_path = os.environ['PATH']
	os.environ['PATH'] = ';'.join((sys_path, dll_dir))
	# Try again
	try:
		libflam4 = CDLL('Flam4CUDA_LIB.dll')
	except WindowsError:
		print("An error has occured loading flam4")
		
LastRenderWidth = 0
LastRenderHeight = 0
cudaRunning = 0


class rgba(Structure):
	_fields_ = [ ('r' , c_float)
				, ('g', c_float)
				, ('b', c_float)
				, ('a', c_float) ]

class xForm(Structure):
	_fields_ = [  ('a', c_float)
				, ('b', c_float)
				, ('c', c_float)
				, ('d', c_float)
				, ('e', c_float)
				, ('f', c_float)
				, ('linear', c_float)
				, ('sinusoidal', c_float)
				, ('spherical', c_float)
				, ('swirl', c_float)
				, ('horseshoe', c_float)
				, ('polar', c_float)
				, ('handkerchief', c_float)
				, ('heart', c_float)
				, ('disc', c_float)
				, ('spiral', c_float)
				, ('hyperbolic', c_float)
				, ('diamond', c_float)
				, ('ex', c_float)
				, ('julia', c_float)
				, ('bent', c_float)
				, ('waves', c_float)
				, ('fisheye', c_float)
				, ('popcorn', c_float)
				, ('exponential', c_float)
				, ('power', c_float)
				, ('cosine', c_float)
				, ('rings', c_float)
				, ('fan', c_float)
				, ('blob', c_float)
				, ('pdj', c_float)
				, ('fan2', c_float)
				, ('rings2', c_float)
				, ('eyefish', c_float)
				, ('bubble', c_float)
				, ('cylinder', c_float)
				, ('perspective', c_float)
				, ('noise', c_float)
				, ('julian', c_float)
				, ('juliascope', c_float)
				, ('blur', c_float)
				, ('gaussian_blur', c_float)
				, ('radial_blur', c_float)
				, ('pie', c_float)
				, ('ngon', c_float)
				, ('curl', c_float)
				, ('rectangles', c_float)
				, ('arch', c_float)
				, ('tangent', c_float)
				, ('square', c_float)
				, ('rays', c_float)
				, ('blade', c_float)
				, ('secant', c_float)
				, ('twintrian', c_float)
				, ('cross', c_float)
				, ('disc2', c_float)
				, ('supershape', c_float)
				, ('flower', c_float)
				, ('conic', c_float)
				, ('parabola', c_float)
				, ('pa', c_float)
				, ('pb', c_float)
				, ('pc', c_float)
				, ('pd', c_float)
				, ('pe', c_float)
				, ('pf', c_float)

				, ('blob_high', c_float)
				, ('blob_low', c_float)
				, ('blob_waves', c_float)
				, ('pdj_a', c_float)
				, ('pdj_b', c_float)
				, ('pdj_c', c_float)
				, ('pdj_d', c_float)
				, ('fan2_x', c_float)
				, ('fan2_y', c_float)
				, ('rings2_val', c_float)
				, ('perspective_angle', c_float)
				, ('perspective_dist', c_float)
				, ('julian_power', c_float)
				, ('julian_dist', c_float)
				, ('juliascope_power', c_float)
				, ('juliascope_dist', c_float)
				, ('radial_blur_angle', c_float)
				, ('pie_slices', c_float)
				, ('pie_rotation', c_float)
				, ('pie_thickness', c_float)
				, ('ngon_power', c_float)
				, ('ngon_sides', c_float)
				, ('ngon_corners', c_float)
				, ('ngon_circle', c_float)
				, ('curl_c1', c_float)
				, ('curl_c2', c_float)
				, ('rectangles_x', c_float)
				, ('rectangles_y', c_float)
				, ('disc2_rot', c_float)
				, ('disc2_twist', c_float)
				, ('supershape_m', c_float)
				, ('supershape_n1', c_float)
				, ('supershape_n2', c_float)
				, ('supershape_n3', c_float)
				, ('supershape_holes', c_float)
				, ('supershape_rnd', c_float)
				, ('flower_holes', c_float)
				, ('flower_petals', c_float)
				, ('conic_holes', c_float)
				, ('conic_eccen', c_float)
				, ('parabola_height', c_float)
				, ('parabola_width', c_float)
			
				, ('color', c_float)
				, ('symmetry', c_float)
				, ('weight', c_float) ]

######################################################
#Should be unused in fr0st - included for completeness
class unAnimatedxForm(Structure):
	_fields_ = [  ('a', c_float)
				, ('b', c_float)
				, ('d', c_float)
				, ('e', c_float) ]
######################################################

class Flame(Structure):
	_fields_ = [  ('center', c_float*2)
				, ('size', c_float*2)
				, ('hue', c_float)
				, ('quality', c_float)
				, ('rotation', c_float)
				, ('symmetryKind', c_float)
				, ('background', rgba)
				, ('brightness', c_float)
				, ('gamma', c_float)
				, ('vibrancy', c_float)
				, ('numTrans', c_int)
				, ('isFinalXform', c_int)
				, ('finalXform', xForm)
				
				,('numColors', c_int)
				,('trans', POINTER(xForm))
				,('transAff', POINTER(unAnimatedxForm))
				,('colorIndex', POINTER(rgba)) ]

libflam4.cuStartCuda.argtypes = [c_uint, c_int, c_int]
libflam4.cuStopCuda.argtypes = []
libflam4.cuRunFuse.argtypes = [POINTER(Flame)]
libflam4.cuStartFrame.argtypes = [POINTER(Flame)]
libflam4.cuRenderBatch.argtypes = [POINTER(Flame)]
libflam4.cuFinishFrame.argtypes = [POINTER(Flame), POINTER(c_ubyte), c_uint]

def loadFlam4(flame):
	flam4Flame = Flame()
	flam4Flame.center[0] = flame.center[0]
	flam4Flame.center[1] = flame.center[1]
	flam4Flame.size[0] = 100./flame.scale
	flam4Flame.size[1] = 100.*(flame.size[1]/flame.size[0])/flame.scale
	flam4Flame.hue = 0								#LINKME
	flam4Flame.quality = 10
	flam4Flame.rotation = flame.rotate
	flam4Flame.symmetry = 0							#LINKME
	flam4Flame.background = rgba(0,0,0,0)			#LINKME
	flam4Flame.brightness = flame.brightness
	flam4Flame.gamma = flame.gamma
	flam4Flame.vibrancy = 1							#LINKME
	flam4Flame.numTrans = len(flame.xform)
	flam4Flame.isFinalXform = 0 if not flame.final else 1
	flam4Flame.numColors = len(flame.gradient)
	palette = (rgba*flam4Flame.numColors)()
	flam4Flame.colorIndex = palette
	for x in range(flam4Flame.numColors):
		flam4Flame.colorIndex[x].r = flame.gradient[x][0]/255.0
		flam4Flame.colorIndex[x].g = flame.gradient[x][1]/255.0
		flam4Flame.colorIndex[x].b = flame.gradient[x][2]/255.0
		flam4Flame.colorIndex[x].a = 1
	xforms = (xForm*flam4Flame.numTrans)()
	flam4Flame.trans = xforms
	uxf = (unAnimatedxForm*flam4Flame.numTrans)()
	flam4Flame.transAff = uxf
	for x in range(len(flame.xform)):
		loadXform(flame.xform[x],flam4Flame.trans[x])
		setTransAff(flam4Flame.transAff[x],flam4Flame.trans[x])
	sum = 0
	for n in range(flam4Flame.numTrans):
		sum = sum+flam4Flame.trans[n].weight
	sum2 = 0
	for  n in range(flam4Flame.numTrans):
		sum2 = sum2+flam4Flame.trans[n].weight/sum
		flam4Flame.trans[n].weight = sum2
	if flam4Flame.isFinalXform:
		loadXform(flame.final, flam4Flame.finalXform)
	return flam4Flame
	
def loadXform(inxform,outxform):
	xform = outxform
	for x in xform._fields_:
		try:
			object.__setattr__(xform, x[0],inxform.__getattribute__(x[0]))
		except AttributeError:
			object.__setattr__(xform, x[0],0)
	post = inxform.post
	xform.b = -xform.b
	xform.d = -xform.d
	xform.f = -xform.f
	xform.pa = post.a
	xform.pb = -post.b
	xform.pc = post.c
	xform.pd = -post.d
	xform.pe = post.e
	xform.py = -post.f
	return xform
	
def setTransAff(transAff, xform):
	transAff.a = xform.a
	transAff.b = xform.b
	transAff.d = xform.d
	transAff.e = xform.e
	
def renderFlam4(flame,size):
	global LastRenderWidth
	global LastRenderHeight
	global cudaRunning
	outputBuffer = (c_ubyte*(size[0]*size[1]*4))()
	if (LastRenderWidth != size[0]) or (LastRenderHeight != size[1]):
		if cudaRunning:
			libflam4.cuStopCuda()
		cudaRunning = 1
		libflam4.cuStartCuda(c_uint(0),c_int(size[0]),c_int(size[1]))
		LastRenderWidth,LastRenderHeight = size
	libflam4.cuStartFrame(pointer(flame))
	for x in range(10):
		libflam4.cuRenderBatch(pointer(flame))
	libflam4.cuFinishFrame(pointer(flame),outputBuffer,0)
	return outputBuffer