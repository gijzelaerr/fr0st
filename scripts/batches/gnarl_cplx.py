# Gnarl + complex FX by Erik Reckase
# Based on a collaboration between Bunny Clarke & Bart Doetsch
#
#  Plugins Required: Tan & Waves2.
# Both can be found in the SuperMassive Plugin Pack @
# http://Fractal-Resources.deviantart.com
#
#  Tips:  T1- Rotate & / or move it. Change size &/or shape. 
#             Try adding or changing variations.
#         T2- Play with variables & small amounts of other 
#             variations. Rotate &/or move it.
#         Final Transform- Move, re-shape, re-size.
#             Add or change variations.

from random import uniform, randint, choice
from fr0stlib.pyflam3.variations import *

from utils import batch

# Customization
# Set selected_var to one of these or 0 for a random selection of spec_vars
spec_vars = [ VAR_EXP, VAR_LOG, VAR_SIN, VAR_COS, VAR_TAN, VAR_SEC, VAR_CSC, VAR_COT,
              VAR_SINH, VAR_COSH, VAR_TANH, VAR_SECH, VAR_CSCH, VAR_COTH ]
selected_var = 0

# End customization

def gnarlcomplex():

    this_var = selected_var
    if this_var==0:
        this_var = choice(spec_vars)        

    # Create new flame
    f = Flame()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    # First Xform
    x = f.add_xform()
    x.a = x.e = -(0.24+uniform(0,0.27))
    x.d = 0.28522
    x.b = -x.d
    x.c = .243505
    x.f = -2.494389
    x.rotate(uniform(0,360))
    x.weight = 0.05
    x.color_speed = 1
    x.color = 0
    x.linear = 0.8+uniform(0,0.22)

    
    # Second Xform
    x = f.add_xform()
    x.coefs = [-0.993819,0.005246,-0.146631,-0.991539,0.799877,-2.399268]
    x.a += uniform(-.001,.001)
    x.b += uniform(-.001,.001)
    x.linear = 0
    x.waves2 = 1
    x.waves2_freqx = randint(4,6);
    x.waves2_scalex = 0.02 + uniform(0,0.03);
    x.waves2_freqy = randint(11,19);
    x.waves2_scaley = -0.02 + uniform(0,0.01);
    x.weight = 7
    x.color = 1
    x.color_speed = 0.01

    # Final X
    fx = f.create_final()
    fx.a = fx.e = -uniform(0.5,1.0)
    fx.d = 0.373412
    fx.b = -fx.d
    fx.c = uniform(0,1)
    fx.f = randint(-1,1) - uniform(0,1)
    fx.rotate(uniform(0,360))
    fx.linear = 0
    setattr(fx,variation_list[this_var],1.0)
    fx.color_speed = 0
    
    
    f.highlight_power = 1.0
    f.gamma = 2
    f.brightness = 5
    f.reframe()

    return f


if __name__ == "__main__":
    lst = batch(gnarlcomplex, 20)
    save_flames("parameters/gnarlcomplex.flame", *lst)


