# Lolpolpolpo, by Coppercat

from random_flame import GenRandomFlame

from fr0stlib.pyflam3.variations import *
import utils,random

# Customize here
###################
rand_angle_min = 15
rand_angle_max = 25
special_vars = (VAR_SPHERICAL,VAR_SWIRL,VAR_WAVES,VAR_POPCORN,
                VAR_BLOB,VAR_JULIAN,VAR_BIPOLAR,VAR_CPOW,
                VAR_LOONIE,VAR_WHORL)
###################
# End customization

# Generate a random batch of flames made from up to 5 linear xforms
randopt = {'xv':(0,), 'n':1, 'xw':0}

def lolpolpolpo():

    # Generate a random flame
    f = GenRandomFlame(randopt, numbasic=5)
    # Normalize weights of xforms in this flame
    # to a sum of 0.5
    utils.normalize_weights(f,norm=0.5)

    # Choose a random xform.  Delete it and create a new one
    # with the same weight using variations in special_vars
    # choosing 3 of them
    delx = random.randint(0,len(f.xform)-1)
    delxw = f.xform[delx].weight
    delcol = f.xform[delx].color
    
    f.xform[delx].delete()

    Xform.random(f, xv=special_vars, n=3, xw=delxw, col=delcol)

    # Add one more all-linear xform with weight 0.5
    # with the magic rotation & offset
    lastx = f.add_xform(weight=0.5, color_speed=0)

    lastx.rotate(random.uniform(rand_angle_min,rand_angle_max))
    lastx.c = random.uniform(-0.5, 0.5)
    lastx.f = random.uniform(-0.5, 0.5)

    # reframe and name the flame
    f.reframe()
    
    return f

if __name__ == "__main__":
    lst = utils.batch(lolpolpolpo, 20)
    save_flames("lolpolpolpo_batch.flame", *lst)


