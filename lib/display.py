import sys

# Hack
if "linux" in sys.platform:
    sys.path.append("/usr/lib/python2.5/site-packages/")

from math import *
from pyflam3 import *

try:
    import pygame
    from pygame import (KMOD_ALT,KMOD_CAPS,KMOD_CTRL,KMOD_LALT,KMOD_LCTRL,
KMOD_LMETA,KMOD_LSHIFT,KMOD_META,KMOD_MODE,KMOD_NONE,KMOD_NUM,KMOD_RALT,
KMOD_RCTRL,KMOD_RMETA,KMOD_RSHIFT,KMOD_SHIFT,K_0,K_1,K_2,K_3,K_4,K_5,K_6,K_7,
K_8,K_9,K_AMPERSAND,K_ASTERISK,K_AT,K_BACKQUOTE,K_BACKSLASH,K_BACKSPACE,K_BREAK,
K_CAPSLOCK,K_CARET,K_CLEAR,K_COLON,K_COMMA,K_DELETE,K_DOLLAR,K_DOWN,K_END,
K_EQUALS,K_ESCAPE,K_EURO,K_EXCLAIM,K_F1,K_F10,K_F11,K_F12,K_F13,K_F14,K_F15,
K_F2,K_F3,K_F4,K_F5,K_F6,K_F7,K_F8,K_F9,K_FIRST,K_GREATER,K_HASH,K_HELP,K_HOME,
K_INSERT,K_KP0,K_KP1,K_KP2,K_KP3,K_KP4,K_KP5,K_KP6,K_KP7,K_KP8,K_KP9,
K_KP_DIVIDE,K_KP_ENTER,K_KP_EQUALS,K_KP_MINUS,K_KP_MULTIPLY,K_KP_PERIOD,
K_KP_PLUS,K_LALT,K_LAST,K_LCTRL,K_LEFT,K_LEFTBRACKET,K_LEFTPAREN,K_LESS,K_LMETA,
K_LSHIFT,K_LSUPER,K_MENU,K_MINUS,K_MODE,K_NUMLOCK,K_PAGEDOWN,K_PAGEUP,K_PAUSE,
K_PERIOD,K_PLUS,K_POWER,K_PRINT,K_QUESTION,K_QUOTE,K_QUOTEDBL,K_RALT,K_RCTRL,
K_RETURN,K_RIGHT,K_RIGHTBRACKET,K_RIGHTPAREN,K_RMETA,K_RSHIFT,K_RSUPER,
K_SCROLLOCK,K_SEMICOLON,K_SLASH,K_SPACE,K_SYSREQ,K_TAB,K_UNDERSCORE,K_UNKNOWN,
K_UP,K_a,K_b,K_c,K_d,K_e,K_f,K_g,K_h,K_i,K_j,K_k,K_l,K_m,K_n,K_o,K_p,K_q,K_r,
K_s,K_t,K_u,K_v,K_w,K_x,K_y,K_z)
except ImportError:
##    raise
    print("Warning: Couldn't import pygame.")
    # Ugly hack or clever trick? you decide!
    pygame = False

try:
    from iterate import iterate
except ImportError:
    print("Warning: Couldn't load shared object.")
    iterate = False


class Display(object):
    
    def _get_size(self):
        return self.width,self.height

    def _set_size(self,v):
        if hasattr(self,'screen'):
            raise AttributeError, "Screen size can't be changed after a frame has been rendered."
        self.width  = v[0]
        self.height = v[1]

    size = property(fget=_get_size,fset=_set_size)

    def _get_alpha(self):
        return self.background.get_alpha()

    def _set_alpha(self,v):
        self.background.set_alpha(v)
    
    background_alpha = property(_get_alpha,_set_alpha)

    width = 640
    height = 480
    quality = 9000
    rc = RandomContext()
    xform_distrib = (c_ushort*10000)()
    iteration = 0
    _tick = 0
    _frames_rendered = 0
    keydown = []
    mask = [ 6,12, 6,
            12,64,12,
             6,12, 6]

    def __init__(self):
        if pygame:
            self.background = pygame.Surface(self.size)
            self.background.set_alpha(8)
        self.pixels = []

    def init(self):
        pygame.init()
        pygame.display.set_caption('Fractal Fr0st')
        alpha = self.background_alpha
        self.background = pygame.Surface(self.size)
        self.background_alpha = alpha
        Array = c_double*(self.quality*4)
        self.samples = Array(flam3_random_isaac_11(self.rc),
                             flam3_random_isaac_11(self.rc),
                             0,
                             1)
        
    def iterate(self,flame):

        # Call the compiled cython code, or fall back to the old way.
        if iterate:
            return iterate(self,flame)
        
        # Local variables
        l_blit = self.screen.blit
        l_samples = self.samples
        l_pixels = self.pixels
        c0,c1 = flame.center
        
        # Precalc some stuff used to project the points to the screen.
        cpx = self.width/4  # 1 complex plane unit, in pixels.
        cpxcos = cos(flame.angle) * cpx
        cpxsin = sin(flame.angle) * cpx
        offset0 = self.width/2 -1  # the -1 compensates for 3x3 pixel size.
        offset1 = self.height/2 -1
        if not self.pixels:
            self.create_pixels(flame)
        else:
            self.update_pixels(flame)

        # Call flam3 functions
        genome = Genome.from_string(flame.to_string(False))[0]
     
        flam3_create_xform_distrib(byref(genome),
                                   cast(self.xform_distrib,POINTER(c_ushort)))

        prepare_xform_fn_ptrs(byref(genome),
                              byref(self.rc))

        flam3_iterate(byref(genome),
                      self.quality,
                      20,
                      cast(l_samples,POINTER(c_double)),
                      cast(self.xform_distrib,POINTER(c_ushort)),
                      byref(self.rc))

        # Draw the results
        for i in range(0,self.quality*4,4):
            x,y,c = l_samples[i:i+3]
            # Rotate
            x -= c0
            y -= c1
            coord = (x*cpxcos + y*cpxsin + offset0,
                     y*cpxcos - x*cpxsin + offset1)            

            try:
                l_blit(l_pixels[int(c*256)],coord)
            except:
                # The point is out of drawable range. It's cheaper to ignore
                # this than check for it at every iteration
                pass
            
        self.iteration += 1

    def create_pixels(self,flame):
        self._oldgradient = flame.gradient[:]
        for r,g,b in flame.gradient:   
            pixel = pygame.Surface((3,3),pygame.SRCALPHA)
            for i in range(9):
                pixel.set_at((i%3,i/3),[r,g,b,self.mask[i]])
            self.pixels.append(pixel)

    def update_pixels(self,flame):
        if flame.gradient == self._oldgradient:
            return
        self._oldgradient = flame.gradient[:]
        for (r,g,b),pixel in zip(flame.gradient, self.pixels):
            for i in range(9):
                pixel.set_at((i%3,i/3),[r,g,b,self.mask[i]])

    def create_screen(self):
        if not hasattr(self,"screen"):
            self.screen = pygame.display.set_mode(self.size)
            self._first_tick = pygame.time.get_ticks()
            self._tick = self._first_tick        

    def process_events(self):
        for e in pygame.event.get():
            if e.type == pygame.KEYUP:
                try:
                    self.keydown.remove(e.key)
                except Exception:
                    pass # Catch mousebottonup?
            elif e.type == pygame.KEYDOWN:
                self.keydown.append(e.key)
            elif e.type == pygame.QUIT:
                self.keydown.append(pygame.K_ESCAPE)

        if pygame.K_ESCAPE in self.keydown:
            pygame.quit()
            sys.exit()            

    def update_screen(self):
        """Updates the screen at a rate of 20 FPS."""

        self.screen.blit(self.background, (0,0))
        
        if pygame.time.get_ticks() > self._tick + 50:           
            pygame.display.flip()
            self._tick += 50
            self._frames_rendered += 1

##        if pygame.time.get_ticks() > 1000 + self._first_tick:
##            print self.iteration * self.quality
##            print "%.1f%% of frames rendered" %(100.*(self._frames_rendered)/self.iteration)
##            pygame.quit()
##            sys.exit()

    def render(self,flame):
        # Creates the screen the first time this function is called
        self.create_screen()

        # Event handling is put here to simplify scripts
        self.process_events()

        self.iterate(flame)

        self.update_screen()


display = Display()
keydown = display.keydown

try:
    display.init()
except:
    print("Warning: Can't initialize the display")
