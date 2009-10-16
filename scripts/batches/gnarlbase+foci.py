# Gnarl Base + Foci by Bunny Clarke and Bart Doetsch
# From original parameters by Golubaja
# Her "Gnarly" gallery is @  http://Golubaja.deviantart.com/
# Foci FX suggested by Zooreka  http://Zooreka.deviantart.com/# TIPS : If there is a hole in the center of the flame - move transforms
# closer together . If flame is too bright - 1 or both Transforms are too
# close to the 0 point of the reference triangle.
# T1 : Add variations, resize, reshape . &/or move it.
# T2 : Do the same. Remember some variations don't "play well " with Waves2.
# T3-T100 : You can't see them yet ( remember this is a "base" ) , these
# Transforms are for you to add & play with.

from random import uniform, randint, choice
from fr0stlib.pyflam3.variations import *

# Customization
# Set selected_var to one of these or 0 for a random selection of spec_vars
# Set selected_var to -1 and get a random variation


spec_vars = [ VAR_POLAR2, VAR_RECTANGLES, VAR_SCRY, VAR_LOONIE, VAR_SINUSOIDAL ]
selected_var = 0

# End customization

def gnarlbasefoci():

    this_var = selected_var
    if this_var==0:
        this_var = choice(spec_vars)
    if this_var==-1:
        this_var = randint(0,len(variation_list)-1)
        

    # Create new flame
    f = Flame()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    # First Xform
    x = f.add_xform()
    x.a = 0.415705
    x.e = 0.415705
    x.rotate(uniform(0,360))
    x.weight = 0.3
    x.color_speed = 0.4
    x.color = uniform(0,1)
    x.c += uniform(0,2)
    x.f += uniform(0,2)
    
    
    # Second Xform
    x = Xform.random(f, xv=(this_var,), n=1, xw=15, col=uniform(0,1), ident=1)
    setattr(x,variation_list[this_var],0.004+uniform(0,0.001))
    x.a = -(0.5-uniform(0,0.01))
    x.b = (0.866+uniform(0,0.01))
    x.c = uniform(0,1)
    
    x.d = -(0.866+uniform(0,0.01))
    x.e = -(0.5-uniform(0,0.01))
    x.f = uniform(0,1)

    x.waves2 = 1
    x.waves2_freqx = randint(-15,-1)
    x.waves2_scalex = 0.01+uniform(0,0.01)
    x.waves2_freqy = randint(14,30)
    x.waves2_scaley = 0.02+uniform(0,0.01)
    
    x.color_speed = 0.1
    
    # Final X
    fx = f.create_final()
    fx.linear = 0
    fx.a = 1.5
    fx.e = 1.5
    fx.foci = 1
    fx.color = uniform(0,1)
    fx.color_speed = 0.2
    
    
    
    f.gamma = 2
    f.brightness = 10
    f.scale = 20

    return f

def gnarlbasefoci_batch(nflames):
    lst = []
    name = "gnarlbase+foci_%03d"
    for i in range(nflames):
        flame = gnarlbasefoci()
        flame.name = name % i
        lst.append(flame)
    return lst

if __name__ == "__main__":
    lst = gnarlbasefoci_batch(20)
    save_flames("parameters/gnarlbasefoci.flame", *lst)


