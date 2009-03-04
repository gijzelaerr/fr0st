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
from _pyapi import *
import _flam3

__all__ = [ 'BufferSizeError', 'from_string', 'file_as_FILE' ]

def file_as_FILE(file):
    """Get the underlying FILE* for a python file
    """
    #TODO: Will this raise an error if it's not a file or fail silently?
    handle = PyFile_AsFile(file)

    if not handle:
        raise RuntimeError('PyFile_AsFile failed')

    return handle


def from_string(s):
    string_len = len(s)
    ptr = _flam3.flam3_malloc(string_len + 1)
    if not ptr:
        raise MemoryError('OH SHI-')

    memset(ptr, 0, string_len+1)
    memmove(ptr, s, string_len)

    return cast(s, c_char_p)



