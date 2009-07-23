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
from __future__ import with_statement
import sys
import os
from _flam3 import *
import marshal as marshal
import _pyapi
from _exceptions import *


class Genome(BaseGenome):

    def _get_size(self):
        return self.width, self.height

    def _set_size(self, value):
        self.width, self.height = value

    size = property(_get_size, _set_size)

    def render(self, **kwargs):
        channels = kwargs.get('channels', 3)
        transparent = kwargs.get('transparent', False) and 1 or 0

        frame = Frame(**kwargs)
        frame.genomes = cast(pointer(self), POINTER(BaseGenome))
        frame.ngenomes = 1

        self.ntemporal_samples = kwargs.get('ntemporal_samples', 1)

##        output_buffer = kwargs.get('buffer', None)
##        if output_buffer:
##            if isinstance(output_buffer, buffer):
##                # standard write buffer objects
##                # allows rendering directly to wxPython Images
##                # through the DataBuffer object
##                ptr = c_void_p()
##                len = _pyapi.Py_ssize_t()
##                _pyapi.PyObject_AsWriteBuffer(output_buffer, byref(ptr), byref(len))
##                if len < (self.width * self.height * channels):
##                    raise BufferTooSmallError("buffer isn't large enough")
##                output_buffer = cast(ptr, POINTER(c_ubyte))
##
##            # otherwise...
##            # try and pass it in, ctypes will tell us if it won't work
##        else:
##            output_buffer = allocate_output_buffer(self.size, channels)

        output_buffer = allocate_output_buffer(self.size, channels)

        stats = RenderStats()
        flam3_render(byref(frame), output_buffer, flam3_field_both, channels, transparent, byref(stats))
        return (output_buffer, stats)

    @classmethod
    def _initialize_genome_list(cls, genomes):
        for i in range(0, len(genomes)):
            if not genomes[i].name:
                genomes[i].name = '%s-%d' % (genomes[i].parent_fname, i)


    @classmethod
    def from_string(cls, input_buffer, filename='<unknown>', defaults=True):
        ncps = c_int()

        #print 'Buffer = ', input_buffer

        # so, flam3_parse_xml2 actually free's the buffer passed in...
        # this hackery sucks but...meh

        # VBT: The next line is replaced by the below block
##        c_buffer = marshal.from_string(input_buffer)
        string_len = len(input_buffer)
        ptr = flam3_malloc(string_len + 1)
        if not ptr:
            raise MemoryError('OH SHI-')

        memset(ptr, 0, string_len+1)

        memmove(ptr, input_buffer, string_len)

        c_buffer = cast(ptr, c_char_p)

        #print string_at(c_buffer)

        result = flam3_parse_xml2(c_buffer, filename,
                defaults and flam3_defaults_on or flam3_defaults_off, byref(ncps))

        genomes = []
        for i in xrange(0, ncps.value):
            genome = cls()
            memmove(byref(genome), byref(result[i]), sizeof(BaseGenome))
            genomes.append(genome)

        #Don't free the input, flam3 already does this.
        #flam3_free(c_buffer)
        flam3_free(result)

        cls._initialize_genome_list(genomes)

        return genomes


    @classmethod
    def from_file(cls, filename=None, handle=None, defaults=True):
        ncps = c_int()

        def open_file(handle):
            return flam3_parse_from_file(marshal.file_as_FILE(handle),
                    os.path.basename(handle.name),
                    defaults and flam3_defaults_on or flam3_defaults_off,
                    byref(ncps))

        if not handle and filename:
            with open(filename, 'rb') as handle:
                if 'win32' in sys.platform:
                    content = handle.read()
                    return cls.from_string(content,
                            filename=os.path.basename(filename))
                else:
                    result = open_file(handle)
        elif handle:
            if 'win32' in sys.platform:
                content = handle.read()
                genomes = cls.from_string(content)
                return cls.from_string(content,
                        filename=os.path.basename(filename))
            else:
                result = open_file(handle)
        else:
            raise IOError('Unable to open file')

        result = cast(result, POINTER(cls))

        genomes = []
        for i in xrange(0, ncps.value):
            genome = cls()
            memmove(byref(genome), byref(result[i]), sizeof(BaseGenome))
            genomes.append(genome) #result[i])

        flam3_free(result)

        cls._initialize_genome_list(genomes)

        return genomes



class Frame(BaseFrame):
    def __init__(self, **kwargs):
        if not kwargs["fixed_seed"]:
            # Initializes the random seed based on system time.
            # A fixed seed is used for preview renders with high noise levels.
            flam3_init_frame(byref(self))

        self.pixel_aspect_ratio = kwargs.get('aspect', 1.0)
        self.temporal_filter_radius = kwargs.get('filter', 1.0)
        self.ngenomes = 0
        self.verbose = kwargs.get('verbose', False) and 1 or 0
        self.bits = kwargs.get('bits', 33)
        self.time = kwargs.get('time', 0)
        self.bytes_per_channel = kwargs.get('bytes_per_channel',1)

        progress = kwargs.get('progress_func', None)
        if callable(progress):
            self.progress = ProgressFunction(progress)
##        else:
##            self.progress = ProgressFunction()
##
##        param = kwargs.get('progress_param', None)
##        if param:
##            if not isinstance(param, py_object):
##                self.progress_parameter = py_object(param)
##            else:
##                self.progress_parameter = param

        self.nthreads = kwargs.get('nthreads', 0)
        if not self.nthreads:
            self.nthreads = flam3_count_nthreads()

