from __future__ import with_statement
import os, atexit, wx

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
                          'waves2',
                          'exp',
                          'log',
                          'sin',
                          'cos',
                          'tan',
                          'sec',
                          'csc',
                          'cot',
                          'sinh',
                          'cosh',
                          'tanh',
                          'sech',
                          'csch',
                          'coth',
                          'auger'),
          "flamepath" : os.path.join("parameters","samples.flame"),
          "Lock-Axes" : True,
          "World-Pivot": False,
          "Variation-Preview": True,
          "Edit-Post-Xform": False,
          "Var-Preview-Settings": {"range": 2,
                                   "numvals": 20,
                                   "depth": 1},
          "Preview-Settings": {"quality": 5,
                               "estimator": 0,
                               "filter_radius": 0},
          "Large-Preview-Settings": {"quality": 25,
                                     "estimator": 0,
                                     "filter_radius": 0.75,
                                     "spatial_oversample":2},
          "Render-Settings": {"quality": 500,
                              "filter_radius": 0.8,
                              "spatial_oversample": 1,
                              "estimator": 9,
                              "estimator_curve": 0.4,
                              "estimator_minimum": 0,
                              "nthreads": 0,
                              "buffer_depth": 33,
                              "earlyclip": False,
                              "transparent": False,
                              "filter_kernel": 0},
          "Gradient-Settings": {"hue": (0, 1),
                                "saturation": (0, 1),
                                "value": (.25, 1),
                                "nodes": (4, 6)},
          "Img-Dir": "renders",
          "Img-Type": ".png",
          "Bits": 0,
          "renderer": "flam3",
          "Rect-Main": None,
          "Rect-Editor": None,
          "Rect-Preview": None,
          }


def get_config_path():
    return os.path.join(wx.GetApp().ConfigDir, 'config.cfg')


def load():
    with open(get_config_path(), 'rb') as f:
        return eval("{%s}" % ",".join(i for i in f))

def dump():
    # HACK: take out some stuff that's not supposed to be here.
    config['Edit-Post-Xform'] = False
    del config["active-vars"]
    
    with open(get_config_path(), 'wb') as f:
        f.write("\n".join("%r: %r" %i for i in config.iteritems()))


def update_dict(old, new):
    for k,v in new.iteritems():
##        if k in old:
            if type(v) == dict:
                update_dict(old[k], v)
            else:
                old[k] = v


def init_config():
    if os.path.exists(get_config_path()):
        _old_config = config.copy()
        update_dict(config, load())
    atexit.register(dump)
