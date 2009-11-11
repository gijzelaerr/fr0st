# Gnarloscope by parrotdolphin
from random import uniform, randint

from utils import batch

# Customization
# VXd:
# 0: random, 1: fisheye+bubble, 2: fisheye+cylinder, 3: wedge_sph
VXd = 0

# VLd:
# 0: random, 1: waves2, 2: linear
VLd = 0

# PBd: (add pre-blur on bubble or cylinder)
# 0: random, 1: yes, 2: no
PBd = 0
# End customization

def gnarloscope():

    if VXd==0:
        VX = randint(1,3)
    else:
        VX = VXd
    
    if VLd==0:
        VL = randint(1,2)
    else:
        VL = VLd
     
    if PBd==0:
        PB = randint(1,2)
    else:
        PB = PBd

    # Create new flame
    f = Flame()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    # First Xform
    x = f.add_xform()
    x.blur = 0.0025
    if VL==1:
        x.linear = 0
        x.waves2 = 1
        x.waves2_freqx = 3 + randint(0,4)
        x.waves2_scalex = 0.05 + uniform(0,0.1)
        x.waves2_freqy = 3 + randint(0,4)
        x.waves2_scaley = 0.05 + uniform(0,0.1)
    
    x.c = uniform(-0.5, 0.5)
    x.f = uniform(-0.5, 0.5)
    x.rotate(uniform(0,360))
    x.scale(1 + uniform(0,0.333))
    x.weight = 1
    x.color_speed = 0.25
    x.color = 0
    x.opacity = 0
    x.animate = 0 # fiddle
    
    # Second Xform
    x = f.add_xform()
    x.linear = 0
    x.juliascope = 1 + uniform(0,0.125)
    x.juliascope_power = 2
    x.juliascope_dist = 1.4 + uniform(0,0.4)
    x.c = uniform(-0.5, 0.5)
    x.f = uniform(-0.5, 0.5)
    x.rotate(uniform(0,360))
    x.scale(1 + uniform(0,0.333))
    x.weight = 1
    x.color_speed = 0
    x.animate = 0 # fiddle
    
    # Third xform
    x = f.add_xform()
    x.linear = 0
    if VX==1: # fisheye + bubble
        myw = uniform(0.4, 0.8)
        x.bubble = myw
        x.fisheye = myw/2.0
        if PB:
            x.pre_blur = uniform(0.15, 0.30)
        x.blur = 0.01
    elif VX==2: # fisheye + cylinder
        myw = uniform(0.2, 0.5)
        x.cylinder = myw
        x.fisheye = myw
        if PB:
            x.pre_blur = uniform(0.15, 0.30)
        x.blur = 0.01
    else: # wedge_sph
        x.wedge_sph = uniform(0.5, 2.0)
        x.wedge_sph_angle = 1.5708
        x.wedge_sph_hole = uniform(-0.5,0.5)
        x.wedge_sph_count = 2
        x.wedge_sph_swirl = 0
    
    x.weight = uniform(0.05, 0.1)
    x.color_speed = 0.75
    x.opacity = 0
    x.color = 1
    x.animate = 1 #fiddle
    
    # randomly change post of third
    if uniform(0,1) > 0.5:
        x.post.c = uniform(-0.5, 0.5)
        x.post.f = uniform(-0.5, 0.5)
        
    f.xform[0].chaos[:] = 0,1,1
    f.xform[1].chaos[:] = 1,0,1
    f.xform[2].chaos[:] = 1,0,1
    
    f.gamma = 3
    f.brightness = 25
    f.scale = 20

    return f

if __name__ == "__main__":
    lst = batch(gnarloscope, 20)
    save_flames("gnarloscopes.flame", *lst)


