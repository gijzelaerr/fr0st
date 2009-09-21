import re, shutil, random, itertools
from math import *

from functions import *

try:
    import wx
except ImportError:
    wx = False

VERSION = "fr0st 0.5 alpha"


class ParsingError(Exception):
    pass



class Flame(object):
    re_flame  = re.compile(r'<flame .*?</flame>',re.DOTALL)
    re_header = re.compile(r'<flame .*?>')
    re_xform  = re.compile(r'<[a-zA-Z]*xform .*?/>')
    re_attr   = re.compile(r'[^ ]*?=".*?(?=")') # Works for xforms and header  

    _default = set(("final","gradient","xform","name", "version"))
    
    def __init__(self, string=""):
        # Set minimum required attributes.
        self.name = "Untitled"
        self.xform = []
        self.size = [512, 384]
        self.center = [0.0, 0.0]
        self.rotate = 0.0
        self.background = [0.0, 0.0, 0.0]
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
                if " " in val: val = map(float,val.split())
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
    

    def create_final(self):
        if not self.final:
            self.final = Xform(self, coefs=[1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                               linear=1, color=0)
        return self.final


    def add_xform(self):
        self.xform.append(Xform(self, coefs=[1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                                linear=1, color=0, weight=1))
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


    def move_center(self, diff):
        """Moves center point, adjusting for any flame rotation."""
        r, phi = polar(diff)
        phi -= self.rotate
        w, h = rect((r, phi))
        self.center[0] += w
        self.center[1] += h        


    def iter_attributes(self):
        return itertools.chain((("name", self.name), ("version", VERSION)),
                               ((k,v) for (k,v) in self.__dict__.iteritems()
                                if k not in self._default))


    @property
    def width(self):
        return self.size[0]
    @width.setter
    def width(self,v):
        self.size[0] = v


    @property
    def height(self):
        return self.size[1]
    @height.setter
    def height(self,v):
        self.size[1] = v


    @property
    def x_offset(self):
        return self.center[0]
    @x_offset.setter
    def x_offset(self, v):
        self.center[0] = v


    @property
    def y_offset(self):
        return self.center[1]
    @y_offset.setter
    def y_offset(self, v):
        self.center[1] = v
    


class Palette(list):
    re_grad = re.compile(r'[0-9A-F]{6}(?=[0-9A-F]*.?$)',re.MULTILINE)
    re_old_grad  = re.compile(r'<color index="[\d]{1,3}" rgb="([\d. ].*)"/>')
    
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

            
    def inverse(self):
        for i in self:
            i = (255 - i[0], 255 - i[1], 255 - i[2])

  
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


    def reverse(self):
        self.reverse()

        
    def from_seed(self, seed, csplit=0, split=30,  dist=64, curve='lin'):
        (h,l,s) = rgb2hls(seed)
        split /= 360.0
        csplit /= 360.0
        comp = hls2rgb((h+csplit+0.5,l,s))
        lspl = hls2rgb((h-split,l,s))
        rspl = hls2rgb((h+split,l,s))

        #from 0 (compliment) to dist (left split)
        g = []
        for i in xrange(dist):
            g.append(tuple(map(int,interp([comp, lspl], dist, i, curve=curve))))
        #from dist to 128 (seed)
        for i in xrange(128-dist):
            g.append(tuple(map(int,interp([lspl, seed], 128-dist, i, curve=curve))))
        #from 127 to 255-dist
        for i in xrange(128-dist):
            g.append(tuple(map(int,interp([seed, rspl], 128-dist, i, curve=curve))))
        #from 255-dist to 255
        for i in xrange(dist):
            g.append(tuple(map(int,interp([rspl, comp], dist, i, curve=curve))))
        
        self[:] = g


    def from_seeds(self, seeds, curve='cos', space='rgb'):
        ns = len(seeds)
        d = 256/ns
        r = 256%ns
        ds = []
        for i in xrange(ns):
            if i+1<=r: ds.append(d+1)
            else:      ds.append(d)
        g = []
        for i in xrange(ns):
            tmp = []
            for j in xrange(ds[i]):
                tmp.append(interp([seeds[i-1], seeds[i]], ds[i], j, curve=curve, c_space=space))
            g += tmp
        self[:] = g

##    """Beginnings of a random generator that takes some ranges"""
##    def random(self, **kwargs):
##        h_ranges = kwargs.get('h_ranges', (0,1))
##        l_ranges = kwargs.get('l_ranges', (0,1))
##        s_ranges = kwargs.get('s_ranges', (0,1))
##        b_range  = kwargs.get('blocks', (32,64))
##        
##        blocks = random.randint(b_range[0],b_range[1])
##        mbs = 256/blocks                        #mean block size
##        mbsr = 256%blocks                       #remainder
##        bsv = mbs/2                             #size variance 1/2 mean
##        bs = []
##        for i in xrange(blocks):
##            v = random.randint(-bsv, bsv)
##            if v<>0: mbsr -= v
##            bs.append(mbs + v)
##        
##        if mbsr>0:
##            r = len(bs)/mbsr
##            for i in xrange(mbsr):
##                bs[(i*r)+random.randrange(r)] += 1
##        elif mbsr<0:
##            r = -len(bs)/mbsr
##            for i in xrange(-mbsr):
##                bs[(i*r)+random.randrange(r)] -= 1
##        tmp = []
##        for b in bs:
##            h = random.random()
##            while not in_ranges(h, h_ranges): h = random.random()
##            l = random.random()
##            while not in_ranges(l, l_ranges): l = random.random()
##            s = random.random()
##            while not in_ranges(s, s_ranges): s = random.random()
##            else:
##                for i in xrange(b):
##                    tmp.append(hls2rgb((h,l,s)))
##        self[:] = tmp


    def random(self, hue=(0,1), saturation=(0,1), value=(0,1),  nodes=(5,5),
               curve='cos'):
        dims = hue, saturation, value
        seeds = [tuple(randrange2(*i) for i in dims)
                 for j in range(randrange2(*nodes, int=int))]
        self.from_seeds(seeds, curve, 'hsv')

        
    def from_image(self, filename, num_tries=50, try_size=1000):
        if not wx:
            raise ImportError('this method requires wx.')
        img = wx.Image(filename)
        orig = []
        for i in xrange(256):
            x = random.randint(0, img.Width-1)
            y = random.randint(0, img.Height-1)
            idx = 3*(x + img.Width*y)
            c = map(ord,img.GetData()[idx:idx+3])
            orig.append(tuple(c))

        best = orig[:]
        len_best = sum(map(pix_diff, best[:-1], best[1:]))
        
        for i in xrange(num_tries):
            pal = orig[:]
            #scramble
            for j in xrange(256):
                pix_swap(pal, i, random.randint(0, 255))
            #measure
            pal_len = sum(map(pix_diff, pal[:-1], pal[1:]))
            #improve
            for j in xrange(try_size):
                i0 = 1 + random.randint(0, 253)
                i1 = 1 + random.randint(0, 253)
                if i0-i1==1:
                    as_is = pix_diff(pal[i1-1], pal[i1]) +\
                            pix_diff(pal[i0], pal[i0+1])
                    swapd = pix_diff(pal[i1-1], pal[i0]) +\
                            pix_diff(pal[i0], pal[i1+1])
                elif i1-i0==1:
                    as_is = pix_diff(pal[i0-1], pal[i0]) +\
                            pix_diff(pal[i1], pal[i1+1])
                    swapd = pix_diff(pal[i0-1], pal[i1]) +\
                            pix_diff(pal[i1], pal[i0+1])
                else:
                    as_is = pix_diff(pal[i0], pal[i0+1]) +\
                            pix_diff(pal[i0], pal[i0-1]) +\
                            pix_diff(pal[i1], pal[i1+1]) +\
                            pix_diff(pal[i1], pal[i1-1])
                    swapd = pix_diff(pal[i1], pal[i0+1]) +\
                            pix_diff(pal[i1], pal[i0-1]) +\
                            pix_diff(pal[i0], pal[i1+1]) +\
                            pix_diff(pal[i0], pal[i1-1])
                if swapd < as_is:
                    pix_swap(pal, i0, i1)
                    pal_len += (swapd - as_is)
            if pal_len < len_best:
                best = pal[:]
                len_best = pal_len
        #---end
        for i in xrange(256):
            i0 = 1 + random.randint(0, 252)
            i1 = i0 + 1
            
            as_is = pix_diff(best[i0-1], best[i0]) +\
                    pix_diff(best[i1], best[i1+1])
            swapd = pix_diff(best[i0-1], best[i1]) +\
                    pix_diff(best[i0], best[i1+1])
            if swapd < as_is:
                holder = pal[i1]
                best[i1] = best[i0]
                best[i0] = holder
                len_best += swapd - as_is
        self[:] = best


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
                post = [1,0,0,1,0,0]
            self._post = PostXform(self, screen_coefs=post)


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

        # Write the post xform.
        lst.append(self.post.to_string())

        # Write the chaos values.
        xaos = self.chaos.get_list()
        if xaos:
            lst.append('chaos="%s " />' % " ".join(map(str,xaos)))
        else:
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
                if k not in self._default and v or hasattr(self.__class__, k))

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
            self._parent.xform.remove(self)



class PostXform(Xform):
    _allowed = set(('coefs', 'points', 'polars', 'screen_coefs', '_parent',
                'a','b','c','d','e','f',
                'x','y','o',
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
        lst.extend(1.0 for i in range(100-len(lst)))
        list.__init__(self, lst)

    def __len__(self):
        if self._parent.isfinal():
            return 0
        return len(self._parent._parent.xform)

    def __iter__(self):
        return (self[i] for i in range(len(self)))
        
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

    def get_list(self):
        lst = list.__getslice__(self,0,len(self))
        for i in reversed(lst):
            if i != 1: break
            lst.pop()
        return lst

#-------------------------------------------------------------------------------
"""
File functions from functions to avoid circular import
"""

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


def load_flames(filename,*args):
    """Reads a flame file and returns a list of flame objects, specified
    by index or name. If no flames are specified, returns all flames in the
    file, in order."""
    
    strings = Flame.load_file(filename)
    
    if not args:
        return [Flame(string=i) for i in strings]

    if all(map(lambda x: type(x) is int, args)):
           return [Flame(string=strings[key]) for key in args]

    flames = []
    re_name = re.compile(r'(?<= name=").*?(?=")')
    temp_names = map(lambda x: re_name.findall(x)[0], strings)

    for key in args:
        _type = type(key)
        if _type is str:
            try:
                key = temp_names.index(key)
            except ValueError:
                raise NameError, ' name "%s" not found in %s' %(key,filename)
        elif _type is not int:
            raise TypeError, "Expected flame index or name, got %s" %_type

        flames.append(Flame(string=strings[key]))
        
    return flames

