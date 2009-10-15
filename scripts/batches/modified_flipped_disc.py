# Modified Flipped Disc by Shortgreenpigg
import random
from fr0stlib.pyflam3.variations import *

# Customization for awesomeness
numbatch = 15
additionalvars = ( range(0,8) + range(9,31)+ [32,33] + range(44,56) )
# End customization

lst = []

for i in range(numbatch):

    # Create new flame
    f = Flame()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    # Choose a random addition variation from the list above
    randv = random.choice(additionalvars)
    randvw = random.uniform(-0.15,0.15)
    
    # Add a transform with disc=0.95 and randv=randvw
    # color = 0, color_speed = 0.05, weight = 2, random rotation and scale it by .4096
    x = Xform.random(f, xv=(VAR_DISC, randv), n=2, xw=2.0, ident=1, col=0)
    x.disc = 0.95
    setattr(x,variation_list[randv],randvw)
    x.scale(0.4096)
    x.color_speed = 0.05
    x.rotate(random.uniform(0,360))
    
    # Add a transform with disc=0.95 and randv=randvw
    # color = 0.701, color_speed = 0.05, weight = 2, random rotation and scale it by .4096
    x2 = Xform.random(f, xv=(VAR_DISC, randv), n=2, xw=2.0, ident=1, col=0.701)
    x2.disc = 0.95
    setattr(x2,variation_list[randv],randvw)
    x2.scale(0.4096)
    x2.color_speed = 0.05
    x2.rotate(random.uniform(0,360))
    x2.post.a = -1.0

    x3 = f.add_xform()
    x3.linear = 0.5
    x3.spherical = 0.5
    x3.radial_blur = 1
    x3.radial_blur_angle = 1
    x3.color = 0.483
    x3.color_speed = 1
    x3.weight = 0.5
    x3.c += 1.0

    x4 = f.add_xform()
    x4.linear = 0.5
    x4.spherical = 0.5
    x4.radial_blur = 1
    x4.radial_blur_angle = 1
    x4.color = 0.0
    x4.color_speed = 1
    x4.weight = 0.5
    x4.c -= 1.0

    f.gamma = 1.89
    f.brightness = 4

    f.scale = random.uniform(55,65)
    f.name = "mod_flipped_disc_%03d" % i
    
    lst.append(f)
    
# Display the batch on the UI
save_flames("parameters/modified_flipped_disc.flame",*lst)

