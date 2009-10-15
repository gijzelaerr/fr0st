# Edisc Julian by Shortgreenpigg
from random import uniform, choice
from fr0stlib.pyflam3.variations import *

def edisc_julian():

    # Create new flame
    f = Flame()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))

    jv = (VAR_JULIAN, VAR_JULIASCOPE)
    
    # Xform 1
    x = f.add_xform()
    x.linear = 0
    if (random.choice(jv) == VAR_JULIAN):
        x.julian = uniform(0.725,0.825)
        x.julian_power = -2
        x.julian_dist = 1
    else:
        x.juliascope = uniform(0.725,0.825)
        x.juliascope_power = -2
        x.juliascope_dist = 1
    
    x.color = uniform(0,1)
    x.color_speed = 0.25
    x.weight = 8
    x.c += 0.39 + uniform(0,0.025)
    x.scale(0.212924)
    
    x.post.a = 1.5625
    x.post.e = 1.5625
    
    ed_weight = uniform(0.3,0.4)
    ed_color = uniform(0,1)
    
    x = f.add_xform()
    x.linear = 0
    x.edisc = ed_weight
    x.color_speed = 0.95
    x.color = ed_color
    x.c += uniform(-1,1)
    x.f += uniform(-1,1)
    x.rotate(uniform(0,360))
    
    x = f.add_xform()
    x.linear = 0
    x.julian = ed_weight
    x.julian_power = 50
    x.julian_dist = -1
    x.color_speed = 0.95
    x.color = ed_color
    
    x = f.add_xform()
    x.linear = 0
    x.julian = ed_weight + 0.08 + uniform(0,0.04)
    x.julian_power = 50
    x.julian_dist = -1
    x.color_speed = 0.95
    x.color = ed_color
    
    f.scale = uniform(12,16)
    f.brightness = 35
    
    return f
    
def edisc_julian_batch(nflames):
    lst = []
    name = "edisc_julian_%03d"
    for i in range(nflames):
        flame = edisc_julian()
        flame.name = name % i
        lst.append(flame)
    return lst

if __name__ == "__main__":
    lst = edisc_julian_batch(20)
    save_flames("parameters/edisc_julians.flame", *lst)


