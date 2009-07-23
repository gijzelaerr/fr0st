from __future__ import with_statement
import cPickle, os, sys, atexit

config = {"active-vars": ('linear',
                          'sinusoidal',
                          'spherical',
                          'swirl',
                          'horseshoe',
                          'polar',
                          'handkerchief',
                          'heart',
                          'disc',
                          'spiral',
                          'hyperbolic',
                          'diamond',
                          'ex',
                          'julia',
                          'bent',
                          'waves',
                          'fisheye',
                          'popcorn',
                          'exponential',
                          'power',
                          'cosine',
                          'rings',
                          'fan',
                          'blob',
                          'pdj',
                          'fan2',
                          'rings2',
                          'eyefish',
                          'bubble',
                          'cylinder',
                          'perspective',
                          'noise',
                          'julian',
                          'juliascope',
                          'blur',
                          'gaussian_blur',
                          'radial_blur',
                          'pie',
                          'ngon',
                          'curl',
                          'rectangles',
                          'arch',
                          'tangent',
                          'square',
                          'rays',
                          'blade',
                          'secant2',
                          'twintrian',
                          'cross',
                          'disc2',
                          'super_shape',
                          'flower',
                          'conic',
                          'parabola',
                          'bent2',
                          'bipolar',
                          'boarders',
                          'butterfly',
                          'cell',
                          'cpow',
                          'curve',
                          'edisc',
                          'elliptic',
                         'escher',
                          'foci',
                          'lazysusan',
                          'loonie',
                          'pre_blur',
                          'modulus',
                          'oscilloscope',
                          'polar2',
                          'popcorn2',
                          'scry',
                          'separation',
                          'split',
                          'splits',
                          'stripes',
                          'wedge',
                          'wedge_julia',
                          'wedge_sph',
                          'whorl',
                          'waves2'),
          "flamepath" : ("parameters","samples.flame"),
          "Lock-Axes" : True,
          "Pivot-Mode": True,
          "Variation-Preview": False,
          "Edit-Post-Xform": False,
          "Var-Preview-Settings": (2, 20, 1),
          }
 

def load():
    with open('config.conf', 'rb') as f:
##        return cPickle.load(f)
        return eval("{%s}" % ",".join(i for i in f))

def dump():
    with open('config.conf', 'wb') as f:
##        cPickle.dump(config, f, cPickle.HIGHEST_PROTOCOL)
        f.write("\n".join("%r: %s" %i for i in config.iteritems()))


if os.path.exists('config.conf'):
    config.update(load())
    
atexit.register(dump)
