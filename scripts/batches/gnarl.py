# Gnarl Batch by ParrotDolphin
from fr0stlib.pyflam3.variations import *

# Customization for awesomeness
# randsides controls the number of sides; set to 0 to choose randomly
# between 3 and 10
randsides = 0
# End customization

def gnarl():
    # Create new flame
    f = Flame()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    RS = randsides or random.randint(3,10)
    
    T1R = RS-2
    T1W = random.uniform(35,45)
    W2SC = random.uniform(0.04, 0.08)
    
    # First Xform
    x = f.add_xform()
    x.linear = 0
    x.waves2 = 1
    x.waves2_freqx = x.waves2_freqy = 5
    x.waves2_scalex = x.waves2_scaley = W2SC
    x.blur = 0.0025
    
    x.scale(random.choice((0.995, 1)))

    x.rotate(-360/float(RS))
    if T1R==1 or T1R==2:
        offset = 4
    elif T1R==3 or T1R==4:
        offset = 3.5
    elif T1R==5 or T1R==6:
        offset = 3
    elif T1R==7:
        offset = 2.5
    elif T1R==8:
        offset = 2
    x.c = random.uniform(-offset, offset)
    x.f = random.uniform(-offset, offset)  
    
    x.weight = T1W
    x.color_speed = 0.01
    x.animate = 0
    x.color = random.uniform(0,1)
    
    ###
    
    T2R =random.randint(1,3)
    
    # Second Xform
    x = f.add_xform()
    x.linear = 0
    if T2R==1:
        x.radial_blur = 0.1 + random.uniform(0,0.7)
    elif T2R==2:
        x.bubble = 0.3 + random.uniform(0,0.7)
        x.radial_blur = 0.1 + random.uniform(0,0.7)
    elif T2R==3:
        x.radial_blur = random.uniform(0,0.1)
        x.julian = 0.1 + random.uniform(0,0.06)
        x.julian_power = 4
        x.julian_dist = 6
    x.weight = 0.5
    x.color_speed = 1
    x.color = random.uniform(0,1)
    x.animate = 1

    # Third Xform
    if random.uniform(0,1)>0.5:
        x = f.add_xform()
        x.e = 0.015; # or is it e
        x.rotate(random.uniform(-45,135))
        x.c = random.uniform(-1,1)
        x.f = random.uniform(-1,1)
        x.weight = 0.5
        x.color_speed = 1
        x.color = random.uniform(0,1)
        x.animate = 1
   
    f.scale = 9
    f.gamma = 4
    f.brightness = 35

    f.reframe()
   
    return f
    
def gnarl_batch(nflames):
    lst = []
    name = "gnarl_%03d"
    for i in range(nflames):
        flame = gnarl()
        flame.name = name % i
        lst.append(flame)
    return lst

if __name__ == "__main__":
    lst = gnarl_batch(20)
    save_flames("parameters/gnarls.flame", *lst)


