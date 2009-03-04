##############################################################################
#  The Combustion Flame Engine - pyflam3
#  http://combustion.sourceforge.net
#
#  Copyright (C) 2007 by Bobby R. Ward <bobbyrward@gmail.com>
#
#  The Combustion Flame Engine is free software; you can redistribute
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

from ctypes import *

__all__ = [ 'Py_ssize_t' 
          , 'PyString_AsStringAndSize'
          , 'PyFile_AsFile'
          , 'PyObject_AsWriteBuffer'
          ]

Py_ssize_t = c_int

# int PyString_AsStringAndSize(PyObject*, char**, int*)
PyString_AsStringAndSize = pythonapi.PyString_AsStringAndSize
PyString_AsStringAndSize.argtypes = (py_object, POINTER(c_char_p), POINTER(Py_ssize_t))
PyString_AsStringAndSize.restype  = c_int

# FILE* PyFile_AsFile(PyObject*)
PyFile_AsFile = pythonapi.PyFile_AsFile
PyFile_AsFile.argtypes = (py_object,)
PyFile_AsFile.restype = c_void_p

# int PyObject_AsWriteBuffer( PyObject *obj, void **buffer, Py_ssize_t *buffer_len)
PyObject_AsWriteBuffer = pythonapi.PyObject_AsWriteBuffer
PyObject_AsWriteBuffer.argtypes = (py_object, POINTER(c_void_p), POINTER(Py_ssize_t))
PyObject_AsWriteBuffer.restype = c_int

