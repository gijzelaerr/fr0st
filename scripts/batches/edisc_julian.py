# Edisc Julian by Shortgreenpigg
import random
from fr0stlib.pyflam3.variations import *

# Customization for awesomeness
numbatch = 15
# End customization

lst = []

jv = (VAR_JULIAN, VAR_JULIASCOPE)

for i in range(numbatch):

    # Create new flame
    f = Flame()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    # Xform 1
    x = f.add_xform()
    x.linear = 0
    if (random.choice(jv) == VAR_JULIAN):
        x.julian = random.uniform(0.725,0.825)
        x.julian_power = -2
        x.julian_dist = 1
    else:
        x.juliascope = random.uniform(0.725,0.825)
        x.juliascope_power = -2
        x.juliascope_dist = 1
    
    x.color = random.uniform(0,1)
    x.color_speed = 0.25
    x.weight = 8
    x.c += 0.39 + random.uniform(0,0.025)
    x.scale(0.212924)
    
    x.post.a = 1.5625
    x.post.e = 1.5625
    
    ed_weight = random.uniform(0.3,0.4)
    ed_color = random.uniform(0,1)
    
    x = f.add_xform()
    x.linear = 0
    x.edisc = ed_weight
    x.color_speed = 0.95
    x.color = ed_color
    x.c += random.uniform(-1,1)
    x.f += random.uniform(-1,1)
    x.rotate(random.uniform(0,360))
    
    x = f.add_xform()
    x.linear = 0
    x.julian = ed_weight
    x.julian_power = 50
    x.julian_dist = -1
    x.color_speed = 0.95
    x.color = ed_color
    
    x = f.add_xform()
    x.linear = 0
    x.julian = ed_weight + 0.08 + random.uniform(0,0.04)
    x.julian_power = 50
    x.julian_dist = -1
    x.color_speed = 0.95
    x.color = ed_color
    
    f.scale = random.uniform(12,16)
    f.brightness = 35
    f.name = "edisc_julian_%03d" % i
    
    lst.append(f)
    
# Display the batch on the UI
save_flames("parameters/edisc_julian.flame",*lst)

