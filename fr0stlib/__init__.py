import re, shutil, random, itertools, Image, numpy, ctypes
from fr0stlib import _utils as utils
from fr0stlib.pyflam3 import Genome,RandomContext,flam3_estimate_bounding_box
from fr0stlib.pyflam3.variations import variable_list,variation_list,variables
from fr0stlib.pyflam3.constants import flam3_nvariations
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
    re_header = re.compile(r'<flame .*?>')
    re_symmetry = re.compile(r'<symmetry kind="(-?\d+)"\s*/>')
    re_xform  = re.compile(r'<[a-zA-Z]*xform .*?/>')
    re_attr   = re.compile(r'[^ ]*?=".*?(?=")') # Works for xforms and header  

    _default = set(("final", "gradient", "xform", "name", "version",
                    "width", "height", "x_offset", "y_offset"))
    
    def __init__(self, string=""):
        # Set minimum required attributes.
        self.name = "Untitled"
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
            self.from_string(string)


    @classmethod
    def load_file(cls,filename):
        """Retrieves all flame data from a flame file and turns it
        into strings."""
        f = open(filename,"r")
        flamestrings = cls.re_flame.findall(f.read())
        f.close()
        return flamestrings

            
    def from_string(self,string):
            
        # Create the gradient
        self.gradient = Palette(string)
                
        # Create the Xform objects
        for xfstr in self.re_xform.findall(string):
            x = Xform.from_string(self, xfstr)

            # Assign the xform to the correct location, 
            if x.weight:
                self.xform.append(x)
            elif not self.final:
                self.final = x
            else:
                raise ParsingError("More than one final xform found")

            
        # Record the header data. This is done after loading xforms so the
        # soloxform fiasco can be safely defused.
        for attr in self.re_attr.findall(self.re_header.search(string).group()):
            name, val = attr.split('="')
                
            # Convert value to the appropriate type
            try:
                if " " in val: val = tuple(float(i) for i in val.split())
                else:          val = float(val)
            except ValueError:
                pass   # Keep as string
            
            setattr(self,name,val)

        # Scale needs to be converted to Apo notation. This is reversed in
        # the to_string method
        self.scale = self.scale * 100 / self.size[0]

        # zoom is deprecated, so scale is adjusted by the zoom value
        if hasattr(self,"zoom"):
            self.scale *= 2**self.zoom
            del self.zoom
            
        sym = self.re_symmetry.findall(string);
        if sym:
            self.add_symmetry(int(sym[0]))
        
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
    

    def _set_soloxform(self, v):
        for xform in self.xform:
            xform.opacity = 1.0 if xform.index == v else 0.0

    soloxform = property(None, _set_soloxform)
    

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
                                ("version", VERSION),
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
    


class Palette(list):
    re_grad = re.compile(r'[0-9A-F]{6}(?=[0-9A-F]*.?$)',re.MULTILINE)
    re_old_grad  = re.compile(r'<color index="[\d]{1,3}" rgb="([\d\. ]*)"/>')
    
    formatstr = ('   <palette count="256" format="RGB">' +
                 32 * ('\n      ' + 24 * '%02X') +
                 '\n   </palette>\n')
    old_formatstr = "".join('   <color index="%s" rgb="%%s %%s %%s"/>\n' %i
                                for i in range(256))
    
    def __init__(self,string=""):
        if string:
            for i in self.re_grad.findall(string):
                self.append((int(i[0:2],16),
                             int(i[2:4],16),
                             int(i[4:6],16)))
            for i in self.re_old_grad.findall(string):
                self.append(map(float, i.split()))
            if len(self) != 256:
                raise ParsingError("Palette data unreadable")
        else:
            for i in xrange(0, 256): self.append((0, 0, 0))


    def to_string(self, newformat=True):
        s = self.formatstr if newformat else self.old_formatstr
        return s % tuple(itertools.chain(*self))


    def rotate(self, index):
        self[:] = self[-index:] + self[:-index]

    
    def hue(self, value):
        value = value/360.0
        for i in xrange(256):
            h,l,s = rgb2hls(self[i])
            h += value
            h = clip(h,0,1,True)
            self[i] = hls2rgb((h,l,s))

            
    def saturation(self, value):
        value = value/100.0
        for i in xrange(256):
            h,l,s = rgb2hls(self[i])
            s += value
            s = clip(s,0,0.999999)
            self[i] = hls2rgb((h,l,s))

            
    def brightness(self, value):
        value = value/100.0
        for i in xrange(256):
            h,l,s = rgb2hls(self[i])
            l += value
            l = clip(l,0,0.999999)
            self[i] = hls2rgb((h,l,s))

            
    def invert(self):
        self[:] = ((255 - i[0], 255 - i[1], 255 - i[2]) for i in self)

  
##    def blur(self, value, space='rgb'):
##        value = clip(value,0,127)
##        tmp = []
##        for i in xrange(0, len(self)):
##            a = self[i-1]
##            b = self[i]
##            if i==len(self)-1: c = self[0]
##            else:            c = self[i+1]
##            if space=='hls':
##                a = rgb2hls(a)
##                b = rgb2hls(b)
##                c = rgb2hls(c)
##            v = value
##            w = 127 - value
##            r = (v*a[0] + 2*w*b[0] + v*c[0])/(4.0*127)
##            g = (v*a[1] + 2*w*b[1] + v*c[1])/(4.0*127)
##            b = (v*a[2] + 2*w*b[2] + v*c[2])/(4.0*127)
##            if space=='hls':
##                color = (hls2rgb((r,g,b)))
##            color = (r,g,b)
##            tmp.append(color)
##        self[:] = tmp

        
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
        
        self[:] = gen


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
        self[:] = gen


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
            self[i] = (best[i,0], best[i,1], best[i,2])


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
    def from_string(cls, parent, string):
        kwds = {}
        for s in parent.re_attr.findall(string):
            name, val = s.split('="')
            try:
                if " " in val: kwds[name] = map(float,val.split())
                else:          kwds[name] = float(val)
            except ValueError:
                kwds[name] = val

        x = Xform(parent, **kwds)
        # Convert from screen to complex plane orientation
        x.coefs = x.screen_coefs
        
        # Symmetry is deprecated, so we factor it into the equivalent attrs.
        x.color_speed = x.__dict__.get("color_speed", (1 - x.symmetry) / 2.0)
        x.animate = x.__dict__.get("animate", float(x.symmetry <= 0))
        x.symmetry = 0.0
            
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
        return 0.0


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


    def _set_plotmode(self, v):
        if v.lower() == "off":
            self.opacity = 0.0
        else:
            raise ValueError('Plotmode can only be set to "off"')
    plotmode = property(None, _set_plotmode)
    
       
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
            xf = Xform.from_string(self._parent,
                                   self.to_string())
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
        lst.extend(1.0 for i in xrange(100))
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
        if pos2 > len(self): pos2 = len(self)
        return list.__getslice__(self,pos,pos2)
    
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
        list.__setslice__(self,pos,pos2,val)

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


def load_flames(filename):
    """Reads a flame file and returns a list of flame objects."""
    return [Flame(string=i) for i in Flame.load_file(filename)]
