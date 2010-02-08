##############################################################################
#  Fractal Fr0st - fr0st
#  https://launchpad.net/fr0st
#
#  Copyright (C) 2009 by Vitor Bosshard <algorias@gmail.com>
#
#  Fractal Fr0st is free software; you can redistribute
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
import os, atexit, wx


def get_config_path():
    return os.path.join(wx.GetApp().ConfigDir, 'config.cfg')

def load():
    with open(get_config_path(), 'rb') as f:
        return eval("{%s}" % ",".join(i for i in f))

def dump():
    # HACK: take out some stuff that's not supposed to be here.
    config['Edit-Post-Xform'] = False
    
    with open(get_config_path(), 'wb') as f:
        f.write("\n".join("%r: %r" %i for i in config.iteritems()))

def update_dict(old, new):
    for k,v in new.iteritems():
        if type(v) == dict:
            update_dict(old[k], v)
        else:
            old[k] = v

config = {}
original_config = {}

def init_config():
    config.update(
         {"flamepath" : os.path.join(wx.GetApp().UserParametersDir,
                                     "samples.flame"),
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
                              "filter_radius": 0.5,
                              "spatial_oversample": 2,
                              "estimator": 9,
                              "estimator_curve": 0.4,
                              "estimator_minimum": 0,
                              "nthreads": 0,
                              "buffer_depth": 64,
                              "earlyclip": True,
                              "transparent": False,
                              "filter_kernel": 0},
          "Gradient-Settings": {"hue": (0, 1),
                                "saturation": (0, 1),
                                "value": (.25, 1),
                                "nodes": (4, 6)},
          "Img-Dir": wx.GetApp().RendersDir,
          "Img-Type": ".png",
          "Bits": 0,
          "renderer": "flam3",
          "Rect-Main": None,
          "Rect-Editor": None,
          "Rect-Preview": None,
          })

    # Make a copy of default values, so they can be restored later.
    original_config.update(config)
    
    if os.path.exists(get_config_path()):
        update_dict(config, load())

    # HACK: if a plain samples.flame is in the config file instead of an
    # absolute path, we need to fix it so it finds the correct location.
    if config["flamepath"] == u"samples.flame":
        config["flamepath"] = original_config["flamepath"]

    atexit.register(dump)
