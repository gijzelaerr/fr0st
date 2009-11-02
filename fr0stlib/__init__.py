import shutil
import random
import itertools
import ctypes
import collections
import xml.etree.cElementTree as etree
import copy
import re

import Image
import numpy
from fr0stlib import _utils as utils
from fr0stlib.pyflam3 import Genome,RandomContext,flam3_estimate_bounding_box
from fr0stlib.pyflam3.variations import variable_list,variation_list,variables
from fr0stlib.pyflam3.constants import flam3_nvariations
from fr0stlib.compatibility import compatibilize
from math import *

from fr0stlib.functions import *

try:
    import wx
except ImportError:
    wx = False


VERSION = "fr0st 0.5 alpha"

_variables = dict([i[0:2] for i in variable_list])

class ParsingError(Exception):
    pass



class Flame(object):
    re_flame  = re.compile(r'<flame .*?</flame>',re.DOTALL)

    _default = set(("final", "gradient", "xform", "name",
                    "width", "height", "x_offset", "y_offset"))
    
    def __init__(self, string=""):
        # Set minimum required attributes.
        self.name = "Untitled"
        self.version = VERSION
        self.xform = []
        self.size = 512, 384
        self.center = [0.0, 0.0]
        self.rotate = 0.0
        self.background = (0.0, 0.0, 0.0)
        self.final = None
        self.scale = 25.
        self.highlight_power = -1
##        self.oversample = 1
##        self.filter = 0.2
##        self.quality = 100
        self.brightness = 4
        self.gamma = 4
        self.gamma_threshold = 0.04
        self.gradient = Palette()
          
        if string:
            root = etree.fromstring(string)
            self.from_element(root)

    @classmethod 	 
    def from_strings(cls, string, type=None): 	 
        """Parses an xml string and returns a list of flames.""" 	 
        type = type or cls 	 
        return [type(i) for i in cls.re_flame.findall(string)]


    def from_element(self, element):
        self.gradient = Palette.from_flame_element(element)

        for xform in element.findall('xform'):
            self.xform.append(Xform.from_element(self, xform))

        self.final = None

        for final in element.findall('finalxform'):
            if self.final is not None:
                raise ParsingError("More than one final xform found")

            self.final = Xform.from_element(self, final)

        # Record the header data. This is done after loading xforms so the
        # soloxform fiasco can be safely defused.
        for name, val in element.items():
            # Convert value to the appropriate type
            try:
                if " " in val: val = tuple(float(i) for i in val.split())
                else:          val = float(val)
            except ValueError:
                pass   # Keep as string
            
            setattr(self,name,val)

        self.name = str(self.name) if hasattr(self, 'name') else None

        # Scale needs to be converted. This is reversed in to_string.
        self.scale = self.scale * 100 / self.size[0]
            
        sym = element.find('symmetry')
        if sym is not None:
            self.add_symmetry(int(sym.get('kind')))

        if self.version != VERSION:
            compatibilize(self, VERSION)

        return self

    def to_string(self, omit_details=False):
        """Extracts parameters from a Flame object and converts them into
        string format."""

        # Make the flame header
        lst =  ['<flame ']
        if omit_details:
            lst.append('name="fr0st" >\n')
        else:
            for name,val in self.iter_attributes():
                ty = type(val)
                if ty in (list, tuple):
                    # Remember to convert round numbers to integer.
                    val = " ".join(str(i if i%1 else int(i)) for i in val)
                elif name == "scale":
                    val = val * self.size[0] / 100
                elif ty in (int, float):
                    val = val if val%1 else int(val)
                lst.append('%s="%s" ' %(name, val))
            lst.append('>\n')           

        # Make each xform
        lst.extend(xform.to_string() for xform in self.iter_xforms())
        
        # Make the gradient
        if not omit_details:
            lst.append(self.gradient.to_string())

        lst.append('</flame>')

        return "".join(lst)


    def __repr__(self):
        return '<flame "%s">' % self.name
    

    def add_final(self, **kwds):
        if self.final:
            return
        defaults = dict(coefs=[1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                        linear=1, color=0, color_speed=0)
        defaults.update(kwds)
        self.final = Xform(self, **defaults)
        return self.final


    def add_xform(self, **kwds):
        defaults = dict(coefs=[1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                        linear=1, color=0, weight=1)
        defaults.update(kwds)
        self.xform.append(Xform(self, **defaults))
        return self.xform[-1]


    def clear(self):
        self.xform = []
        self.final = None


    def copy(self):
        return Flame(string=self.to_string())

#    def copy(self):
#        self.xform, xforms = [], self.xform
#
#        new_flame = copy.deepcopy(self)
#
#        for xform in xforms:
#            new_xform = xform.copy()
#            new_xform._parent = new_flame
#            new_flame.xform.append(new_xform)
#
#        self.xform = xforms
#
#        return new_flame
    


    def iter_xforms(self):
        for i in self.xform:
            yield i
        if self.final:
            yield self.final

    def iter_posts(self):
        for i in self.iter_xforms():
            if i.post.isactive():
                yield i.post


    @property
    def angle(self):
        return radians(self.rotate)
    @angle.setter
    def angle(self,v):
        self.rotate = degrees(v)

    def reframe(self):
        TwoDoubles = ctypes.c_double * 2

        b_min = TwoDoubles()
        b_max = TwoDoubles()
        b_eps = 0.01
        nsamples = 10000
        genome = Genome.from_string(self.to_string(False))[0]
        flam3_estimate_bounding_box(genome, b_eps, nsamples, b_min, b_max, RandomContext())
        #print "%f %f" % ((b_min[0]+b_max[0])/2,(b_min[1]+b_max[1])/2)
        bxoff = (b_min[0]+b_max[0])/2
        if abs(bxoff)<5:
            self.x_offset = bxoff

        byoff = (b_min[1]+b_max[1])/2
        if abs(byoff)<5:
            self.y_offset = byoff
            
        denom = min(b_max[1]-b_min[1],b_max[0]-b_min[0])

        if denom==0:
            tmpscale = 0.0
        else:
            tmpscale = 0.7 * 100.0/min(b_max[1]-b_min[1],b_max[0]-b_min[0])
        
        if tmpscale<10:
            self.scale = 10
        elif tmpscale>100:
            self.scale = 100
        else:
            self.scale = tmpscale
            
    def add_symmetry(self,sym):
        """Adds xforms as per symmetry tag - sym=0 chooses random symmetry"""
        if sym==0:
            sym_distrib = (-4, -3, -2, -2, -2, -1, -1, -1, 2, 2, 2, 3, 3, 4, 4)
            sym = random.choice(sym_distrib)
            
        if sym==0 or sym==1:
            return
            
        if sym<0:
            x = self.add_xform()
            x.weight = 1.0
            x.color_speed = 0.0
            x.animate = 0.0
            x.color = 1.0
            x.a = -1.0
            sym = -sym
        
        srot = 360.0 / float(sym)
        
        for k in range(1,sym):
            x = self.add_xform()
            x.weight = 1.0
            x.color_speed = 0.0
            x.animate = 0.0
            if (sym<3):
                x.color = 0.0
            else:
                x.color = (k-1.0)/(sym-2.0)
            
            x.rotate(k*srot)

    def move_center(self, diff):
        """Moves center point, adjusting for any flame rotation."""
        r, phi = polar(diff)
        phi -= self.rotate
        w, h = rect((r, phi))
        self.x_offset += w
        self.y_offset += h        


    def iter_attributes(self):
        return itertools.chain((("name", self.name),
                                ("size", self.size),
                                ("center", self.center)),
                               ((k,v) for (k,v) in self.__dict__.iteritems()
                                if k not in self._default))

    
    @property
    def size(self):
        return self.width, self.height
    @size.setter
    def size(self, v):
        self.width, self.height = v


    @property
    def center(self):
        return self.x_offset, self.y_offset
    @center.setter
    def center(self, v):
        self.x_offset, self.y_offset = v


class Palette(collections.Sequence):
    def __init__(self, string=None):
        self.data = numpy.zeros((256, 3), dtype=numpy.uint8)

    def __len__(self):
        return 256

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

#    def __contains__(self, value):
#        return NotImplementedError("contains makes no sense on palettes")

    def to_string(self):
        s = '   <color index="%s" rgb="%s %s %s"/>\n'
        return ''.join([s % (idx, int(self.data[idx, 0]), int(self.data[idx, 1]), int(self.data[idx, 2])) for idx in xrange(256)])

    @classmethod
    def from_flame_element(cls, flame):
        palette_element = flame.find('palette')
        palette = cls()

        if palette_element is not None:
            if int(palette_element.get('count')) != 256:
                raise ParsingError('Palette must contain 256 entries')

            if palette_element.get('format').strip().lower() != 'rgb':
                raise ParsingError('Only rgb palettes are currently supported')

            data = ''.join(palette_element.text.split())

            for idx in range(0, len(data), 6):
                palette.data[idx/6, 0] = int(data[idx+0:idx+2], 16)
                palette.data[idx/6, 1] = int(data[idx+2:idx+4], 16)
                palette.data[idx/6, 2] = int(data[idx+4:idx+6], 16)

            if idx != 255 * 6:
                raise ParsingError('Not enough palette entries specified: %s != %s' % (255 * 6, idx))

        else:
            for color in flame.findall('color'):
                r, g, b = color.get('rgb').split()
                index = int(color.get('index'))
                palette.data[index, 0] = float(r)
                palette.data[index, 1] = float(g)
                palette.data[index, 2] = float(b)

        return palette


    def rotate(self, index):
        self.data = numpy.array(
                list(self.data[-index:]) + list(self.data[:-index]), dtype=numpy.uint8)

    def hue(self, value):
        value = value/360.0
        for i in xrange(256):
            h,l,s = rgb2hls(self.data[i])
            h += value
            h = clip(h,0,1,True)
            rgb = hls2rgb((h,l,s))
            self.data[i] = hls2rgb((h,l,s))

            
    def saturation(self, value):
        value = value/100.0
        for i in xrange(256):
            h,l,s = rgb2hls(self.data[i])
            s += value
            s = clip(s,0,1)
            self.data[i] = hls2rgb((h,l,s))

            
    def brightness(self, value):
        value = value/100.0
        for i in xrange(256):
            h,l,s = rgb2hls(self.data[i])
            l += value
            l = clip(l,0,1)
            self.data[i] = hls2rgb((h,l,s))

            
    def invert(self):
        self.data = 255 - self.data

        
    def from_seed(self, seed, csplit=0, split=30,  dist=64, curve='lin'):
        (h,l,s) = rgb2hls(seed)
        split /= 360.0
        csplit /= 360.0
        comp = hls2rgb((h+csplit+0.5,l,s))
        lspl = hls2rgb((h-split,l,s))
        rspl = hls2rgb((h+split,l,s))
        if curve=='lin': cur = 0
        elif curve=='cos': cur = 1
        else: raise ValueError('Curve must be lin or cos')

        #from 0 (compliment) to dist (left split)
        gen = []
        for i in xrange(dist):
            r = utils.pblend(comp[0], lspl[0], (i/float(dist)), cur)
            g = utils.pblend(comp[1], lspl[1], (i/float(dist)), cur)
            b = utils.pblend(comp[2], lspl[2], (i/float(dist)), cur)
            gen.append((r, g, b))
        #from dist to 128 (seed)
        for i in xrange(128-dist):
            r = utils.pblend(lspl[0], seed[0], (i/float(128-dist)), cur)
            g = utils.pblend(lspl[1], seed[1], (i/float(128-dist)), cur)
            b = utils.pblend(lspl[2], seed[2], (i/float(128-dist)), cur)
            gen.append((r, g, b))
        #from 127 to 255-dist
        for i in xrange(128-dist):
            r = utils.pblend(seed[0], rspl[0], (i/float(128-dist)), cur)
            g = utils.pblend(seed[1], rspl[1], (i/float(128-dist)), cur)
            b = utils.pblend(seed[2], rspl[2], (i/float(128-dist)), cur)
            gen.append((r, g, b))
        #from 255-dist to 255
        for i in xrange(dist):
            r = utils.pblend(rspl[0], comp[0], (i/float(dist)), cur)
            g = utils.pblend(rspl[1], comp[1], (i/float(dist)), cur)
            b = utils.pblend(rspl[2], comp[2], (i/float(dist)), cur)
            gen.append((r, g, b))
        
        self.data = numpy.array(gen, dtype=numpy.uint8)


    def from_seeds(self, seeds, curve='cos'):
        if curve=='lin': cur = 0
        elif curve=='cos': cur = 1
        else: raise ValueError('Curve must be lin or cos')
        ns = len(seeds)
        d = 256/ns
        r = 256%ns
        ds = []
        for i in xrange(ns):
            if i+1<=r: ds.append(d+1)
            else:      ds.append(d)
        gen = []
        for i in xrange(ns):
            for j in xrange(ds[i]):
                h = utils.pblend(seeds[i-1][0], seeds[i][0], (j/float(ds[i])), cur)
                s = utils.pblend(seeds[i-1][1], seeds[i][1], (j/float(ds[i])), cur)
                v = utils.pblend(seeds[i-1][2], seeds[i][2], (j/float(ds[i])), cur)
                gen.append(hsv2rgb((h,s,v)))
        self.data = numpy.array(gen, dtype=numpy.uint8)


    def random(self, hue=(0,1), saturation=(0,1), value=(0,1),  nodes=(5,5),
               curve='cos'):
        dims = hue, saturation, value
        seeds = [tuple(randrange2(*i) for i in dims)
                 for j in range(randrange2(*nodes, int=int))]
        self.from_seeds(seeds, curve)

        
    def from_image(self, filename, num_tries=50, try_size=1000):
        img = Image.open(filename)
        bin = map(ord, img.tostring())
        grab = numpy.zeros((256, 3), numpy.float32)
        for i in xrange(256):
            x = random.randint(0, img.size[0]-1)
            y = random.randint(0, img.size[1]-1)
            idx = 3*(x + img.size[0]*y)
            grab[i] = bin[idx:idx+3]

        best = utils.palette_improve(grab, num_tries, try_size)
        for i in xrange(256):
            self.data[i] = (best[i,0], best[i,1], best[i,2])


class Xform(object):
    """Container for transform parameters."""

    _default = set(("_parent","a","b","c","d","e","f","_chaos","_post"))
    # We need to specify attributes with an explicit default value.
    # See iter_attributes for more details.
    opacity = 1.0
    color = 0.0
    color_speed = 0.5
    animate = 1.0

    def __init__(self, parent=None, chaos=None, post=None, **kwds):
        self._parent = parent

        map(self.__setattr__, *zip(*kwds.iteritems()))
        
        # Create default values. Subclasses ignore this.
        if type(self) is Xform:
            if chaos is None:
                chaos = [1.0]
            self._chaos = Chaos(self, chaos)
            
            if post is None:
                post = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
            self._post = PostXform(self, screen_coefs=post)


    @classmethod
    def random(cls, parent, xv=range(flam3_nvariations), n=1, xw=0, fx=0, col=0, ident=0, **kwds):

        # We can't add a final xform if one already exists
        if parent.final and fx>0:
            return None
        
        # Add a standard xform, or a final if the randomness permits
        if fx==0:
            x = parent.add_xform()
        elif random.uniform(0,1)<=fx:
            x = parent.add_final()
        else:
            return None
        
        # Clear out the linearness
        x.linear=0
        
        # Randomize the coefficients
        if not ident:
            x.coefs = (random.uniform(-1,1) for i in range(6))
        
            if random.uniform(0,1)>0.7:
                x.c = 0.0
                x.f = 0.0
        
        if not x.isfinal():
            if xw>0: # If weight is > 0, set the weight directly
                x.weight = xw
            elif xw<0: # Weight < 0 means randomize from 0 to -xw
                x.weight = random.uniform(0,-xw)
            else: # Random from 0 to 1
                x.weight = random.uniform(0.1,1)
        
        # Select the variations to use
        use_vars = random.sample(xv,n)
        for uv in use_vars:
            setattr(x,variation_list[uv],random.uniform(-1,1))
            for p,v in variables[variation_list[uv]]:
                setattr(x, "%s_%s" % (variation_list[uv],p), v())
            
        x.color = col
        
        if fx==0:
            x.animate=1
            
        return x

    @classmethod
    def from_element(cls, parent, element):
        kwds = {}

        for name, val in element.items():
            try:
                if " " in val: kwds[name] = map(float,val.split())
                else:          kwds[name] = float(val)
            except ValueError:
                kwds[name] = val

        x = Xform(parent, **kwds)
        # Convert from screen to complex plane orientation
        x.coefs = x.screen_coefs

        return x

    def to_string(self):
        lst = ['   <%sxform '%("final" if self.isfinal() else "")]
        lst.extend('%s="%s" ' %i for i in self.iter_attributes())
        lst.append('coefs="%s %s %s %s %s %s" ' % self.screen_coefs)
        lst.append(self.post.to_string())
        lst.append(self.chaos.to_string())
        lst.append('/>\n')
        
        return "".join(lst)
    
            
    def __repr__(self):
        try:
            index = self.index
        except ValueError:
            # For some reason, the xform is not found inside the parent
            return "<xform>"
        if index is None:
            return "<finalxform>"
        return "<xform %d>" %(index + 1)

      
    def __getattr__(self,v):
        """Returns a default value for non-existing attributes"""
        # __getattribute__ is the real lookup special method,  __getattr__ is
        # only called when it fails.
        if v in variation_list:
            return 0.0

        if v in self._default:
            return 0.0

        if v in ('symmetry', 'plotmode', 'index', 'weight'):
            return 0.0

        raise AttributeError(v)

    @property
    def chaos(self):
        return self._chaos
    @chaos.setter
    def chaos(self,v):
        if type(v) is not Chaos:
            raise TypeError, "The chaos attribute requires a Chaos object"
        self._chaos = v


    @property
    def post(self):
        return self._post
    @post.setter
    def post(self,v):
        if type(v) is not PostXform:
            raise TypeError, "The post attribute requires a PostXform object"
        self._post = v


    @property
    def index(self):
        if self is self._parent.final:
            return None
        return self._parent.xform.index(self)
    
       
    @property
    def coefs(self):
        return self.a,self.d,self.b,self.e,self.c,self.f
    @coefs.setter
    def coefs(self,v):
        self.a,self.d,self.b,self.e,self.c,self.f = v

       
    @property
    def screen_coefs(self):
        return self.a,-self.d,-self.b,self.e,self.c,-self.f
    @screen_coefs.setter
    def screen_coefs(self, v):
        self.coefs = v
        self.d = -self.d
        self.b = -self.b
        self.f = -self.f


    def list_variations(self):
        return [i for i in variations if i in self.__dict__]


    def iter_attributes(self):
        return ((k,v) for (k,v) in self.__dict__.iteritems()
                if k not in self._default and v or hasattr(self.__class__, k)
                or k in _variables)

#----------------------------------------------------------------------

    @property
    def pos(self):
        return self.c, self.f
    @pos.setter
    def pos(self, v1, v2=None):
        if v2 is None: v1, v2 = v1
        self.c = v1
        self.f = v2

    def move_pos(self,v1,v2=None):
        if v2 is None: v1, v2 = v1       
        self.c += v1
        self.f += v2

#----------------------------------------------------------------------
       
    @property        
    def x(self):
        return self.a + self.c, self.d + self.f
    @x.setter
    def x(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.a  = v1 - self.c
        self.d  = v2 - self.f

    def move_x(self,v1,v2=None):     
        if v2 is None: v1, v2 = v1  
        self.a += v1
        self.d += v2

       
    @property
    def y(self):
        return self.b + self.c, self.e + self.f
    @y.setter
    def y(self, v1, v2=None):
        if v2 is None: v1, v2 = v1
        self.b  = v1 - self.c
        self.e  = v2 - self.f

    def move_y(self, v1, v2=None):     
        if v2 is None: v1, v2 = v1 
        self.b += v1
        self.e += v2

       
    @property
    def o(self):
        return self.c, self.f
    @o.setter
    def o(self, v1, v2=None):
        if v2 is None: v1, v2 = v1
        self.a += self.c - v1
        self.d += self.f - v2
        self.b += self.c - v1
        self.e += self.f - v2
        self.c  = v1
        self.f  = v2


    def move_o(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.a -= v1
        self.d -= v2
        self.b -= v1
        self.e -= v2
        self.c += v1
        self.f += v2

    @property
    def points(self):
        return self.x,self.y,self.o
    @points.setter
    def points(self, v):
        self.x,self.y,self.o = v

#----------------------------------------------------------------------
       
    @property    
    def xp(self):
        return polar((self.a, self.d))
    @xp.setter
    def xp(self, coord):
        self.a, self.d = rect(coord)

       
    @property
    def yp(self):
        return polar((self.b, self.e))
    @yp.setter
    def yp(self, coord):
        self.b, self.e = rect(coord)

       
    @property
    def op(self):
        return polar((self.c, self.f))
    @op.setter
    def op(self, coord):
        self.c, self.f = rect(coord)

       
    @property
    def polars(self):
        return self.xp, self.yp, self.op
    @polars.setter
    def polars(self, coord):
        self.xp, self.yp, self.op = coord

#----------------------------------------------------------------------

    def scale_x(self, v):
        self.a *= v
        self.d *= v

    def scale_y(self, v):
        self.b *= v
        self.e *= v
        
    def scale(self,v):
        self.a *= v
        self.d *= v
        self.b *= v
        self.e *= v

        
    def rotate_x(self, deg):
        self.xp = (self.xp[0], self.xp[1] + deg)
        
    def rotate_y(self, deg):
        self.yp = (self.yp[0], self.yp[1] + deg)

    def rotate(self, deg, pivot=None):
        self.rotate_x(deg)
        self.rotate_y(deg)
        if pivot is not None:
            self.orbit(deg,pivot)
            
        
    def move(self,v):
        self.op = (self.op[0] + v, self.op[1])


    def orbit(self,deg,pivot=(0,0)):
        """Orbits the transform around a fixed point without rotating it."""
        if pivot == (0,0):
            self.op = (self.op[0], self.op[1] + deg)
        else:
            hor = self.c - pivot[0]
            ver = self.f - pivot[1]   
            angle  = atan2(hor,ver) - radians(deg)
            
            vector = hypot(hor,ver)
            self.c = pivot[0] + sin(angle) * vector
            self.f = pivot[1] + cos(angle) * vector

#----------------------------------------------------------------------

    def ispost(self):
        return type(self._parent) == Xform


    def isfinal(self):
        return self.index is None

    
    def copy(self):
        if not self.isfinal():
            self._parent, parent = None, self._parent
            self._chaos, chaos = None, self._chaos
            self.post._parent = None
            xf = copy.deepcopy(self)

            xf.post._parent = xf
            xf._parent = parent

            self._chaos = chaos
            self._parent = parent
            self.post._parent = self

            xf._chaos = Chaos(xf, chaos)

            self._parent.xform.append(xf)

            return xf


    def delete(self):
        if self.isfinal():
            self._parent.final = None            
        else:
            index = self.index
            self._parent.xform.remove(self)
            for x in self._parent.xform:
                del x.chaos[index]



class PostXform(Xform):
    _allowed = set(('coefs', 'points', 'polars', 'screen_coefs', '_parent',
                'a','b','c','d','e','f',
                'x','y','o','pos',
                'xp','yp','op'))

    def __repr__(self):
        return "<post-%s" % repr(self._parent)[1:]

    def __setattr__(self,name,v):
        if name not in self._allowed:
            raise AttributeError, 'Can\'t assign "%s" to %s' %(name,self)
        object.__setattr__(self,name,v)

    def copy(self):
        raise TypeError, "Can't copy a post transform"

    def delete(self):
        raise TypeError, "Can't delete a post transform"

    def isactive(self):
        return self.coefs != (1,0,0,1,0,0)

    def to_string(self):
        if self.isactive():
            return 'post="%s %s %s %s %s %s" ' % self.screen_coefs
        return ""



class Chaos(list):
    """ A list which returns 1 for unassigned items, and pads the list when
    necessary to store values in their correct locations."""

    def __repr__(self):
        return "Chaos(%s)" %self[:]

    def __init__(self, parent, lst):
        self._parent = parent
        lst = map(float, lst)
        # HACK: 100 extra items could run out in theory. However, it's
        # complicated to do a "proper" implementation of this, due to the slice
        # methods.
        lst.extend([1] * 100)
        list.__init__(self, lst)

    def __len__(self):
        if self._parent.isfinal():
            return 0
        return len(self._parent._parent.xform)

    def __iter__(self):
        return (self[i] for i in xrange(len(self)))
        
    def __getitem__(self,pos):
        if abs(pos) > len(self)-1:
            raise IndexError
        return list.__getitem__(self,pos)

    def __getslice__(self,pos,pos2):
        if (pos<0) or (pos2<0):
            raise NotImplementedError, "Negative slicing not supported"
        return list.__getslice__(self,pos, min(pos2, len(self)))
    
    def __setitem__(self,pos,val):
        if val < 0:
            raise ValueError(val)
        if abs(pos) > len(self)-1:
            raise IndexError(pos)
        list.__setitem__(self,pos,val)
      
    def __setslice__(self,pos,pos2,val):
        if any(i < 0 for i in val):
            raise ValueError(val)
        if (pos<0) or (pos2<0):
            raise NotImplementedError, "Negative slicing not supported"
        list.__setslice__(self, pos, min(pos2, len(self)), val)

    def to_string(self):
        lst = self[:]
        for i in reversed(lst):
            if i != 1:
                break
            lst.pop()
        return 'chaos="%s " ' % " ".join(str(i) for i in lst) if lst else ""



def save_flames(filename,*flames):
    lst = [f.to_string() if isinstance(f,Flame) else f for f in flames]
    lst.insert(0, """<flames name="Fr0st Batch">""")
    lst.append("""</flames>""")
    head, ext = os.path.splitext(filename)
    if os.path.exists(filename) and ext == ".flame":
        shutil.copy(filename,head + ".bak")
    f = open(filename,"w")
    f.write("\n".join(lst))
    f.close()


def load_flame_strings(filename):
    with open(filename) as fd:
        s = fd.read()

    return Flame.from_strings(s, str)

def load_flames(filename):
    """Reads a flame file and returns a list of flame objects."""
    with open(filename) as fd:
        tree = etree.parse(fd)

    return [Flame().from_element(e) for e in tree.findall('flame')]


def show_status(s):
    sys.stdout.write("%s\r" %s)
