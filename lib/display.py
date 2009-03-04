import sys

# Hack
if "linux" in sys.platform:
    sys.path.append("/usr/lib/python2.5/site-packages/")

import pygame
from math import *

from pyflam3 import *
from pyflam3.variations import variations
from lib._exceptions import ThreadInterrupt

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
            raise ThreadInterrupt
##            pygame.quit()
##            sys.exit()            

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
