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


class Genome(BaseGenome):

    def _get_size(self):
        return self.width, self.height

    def _set_size(self, value):
        self.width, self.height = value

    size = property(_get_size, _set_size)

    def render(self, channels=3, transparent=False, ntemporal_samples=1,
               temporal_filter=1.0, estimator=9, **kwargs):
        
        self.ntemporal_samples = ntemporal_samples
        self.temporal_filter_width = temporal_filter
        self.estimator = estimator
        # TODO: add:
        # spatial_oversample,
        # spatial_filter (why is there a radius/select?)
        
        frame = Frame(**kwargs)
        frame.genomes = cast(pointer(self), POINTER(BaseGenome))
        frame.ngenomes = 1

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

        # so, flam3_parse_xml2 actually free's the buffer passed in...
        # this hackery sucks but...meh

        string_len = len(input_buffer)
        ptr = flam3_malloc(string_len + 1)
        if not ptr:
            raise MemoryError('OH SHI-')

        memset(ptr, 0, string_len+1)

        memmove(ptr, input_buffer, string_len)

        c_buffer = cast(ptr, c_char_p)

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
    def __init__(self, fixed_seed=False, aspect=1.0, bits=33, time=0,
                 bytes_per_channel=1, progress_func=None, nthreads=0,
                 **kwargs):
        if not fixed_seed:
            # Initializes the random seed based on system time.
            # A fixed seed is used for preview renders with high noise levels.
            flam3_init_frame(byref(self))

        self.pixel_aspect_ratio = aspect
        self.ngenomes = 0
        self.bits = bits
        self.time = time
        self.bytes_per_channel = bytes_per_channel

        if callable(progress_func):
            self.progress = ProgressFunction(progress_func)

        if nthreads:
            self.nthreads = nthreads
        else:
            self.nthreads = flam3_count_nthreads()

