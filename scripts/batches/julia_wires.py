# Julia Wires by Shortgreenpigg
from fr0stlib.pyflam3.variations import *
from random import uniform,randint,choice

# Customization for awesomeness
numbatch = 15
# End customization

lst = []

tubevars = ( range(0,14) + [15,17,21,25,32,33] + 
             range(35,41) + [42,46,48,49,51,52] +
             range(54,65) )

for i in range(numbatch):

    # Create new flame
    f = Flame()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    # Xform 1
    x = f.add_xform()
    x.linear = 0
    j = randint(0,3)
    if j==0:
        x.noise = uniform(0,0.2)
    elif j==1:
        x.blur = uniform(0,0.1)
    elif j==2:
        x.gaussian_blur = uniform(0,0.2)
    else:
        x.bubble = uniform(0,0.1)
    
    x.rotate(uniform(0,360))
    x.c += uniform(-1,1)
    x.f += uniform(-1,1)
    x.weight = 0.25  # tweak
    x.color_speed = 0.9
    x.color = 0.5
    
    x = f.add_xform()
    x.linear = 0
    x.julian = 1 # tweak
    x.julian_power = 2 # tweak
    x.julian_dist = -1 #tweak
    x.rotate(uniform(0,360))
    x.c += uniform(-0.5,0.5)
    x.f += uniform(-0.5,0.5)
    x.scale(0.5) # tweak
    x.weight = 0.5 #tweak
    x.color = 1
    
    myvar = choice(tubevars)
    if myvar==VAR_JULIAN:
        x = Xform.random(f,xv=(VAR_JULIAN,VAR_JULIASCOPE),n=2,xw=0.25,ident=1,col=0)
        x.julian = uniform(1,2)
        x.julian_power = uniform(4,8)
        x.julian_dist = 1
        x.juliascope = 0.25 + uniform(0,1)
        x.juliascope = uniform(20,40)
        x.juliascope_dist = 1
    else:
        x = Xform.random(f,xv=(VAR_JULIAN,myvar),n=2,xw=0.25,ident=1,col=0)
        x.julian = uniform(.25, 1.25)
        x.julian_power = uniform(15,45)
        x.julian_dist = 1
        setattr(x,variation_list[myvar],uniform(1,2))
    
    x.d = -0.5
    x.e = 0
    x.c = uniform(-1,1)
    x.f = uniform(-1,1)
    x.rotate(uniform(0,360))
    x.scale(2)
    
    x = f.add_xform()
    x.linear = 0
    x.julian = 1
    x.julian_power = uniform(2,8)
    x.julian_dist = 1
    x.rotate(uniform(0,360))
    x.scale(0.5)
    x.c = uniform(-1,1)
    x.f = uniform(-1,1)
    x.weight = 0.25
    x.color_speed = 0.9
    x.color = 0
    
    xf = f.create_final()
    xf.linear = 0
    xf.spherical = uniform(.5,1.5)
    xf.julia = uniform(.25,1.25)
    xf.color_speed = 0
    xf.c = uniform(0,1.5)-.75
    xf.f = uniform(0,1.5)-.75
    xf.rotate(uniform(0,360))

    f.reframe()

    f.name = "julia_wires_%03d" % i
    
    lst.append(f)
    
# Display the batch on the UI
save_flames("parameters/julia_wires.flame",*lst)
    
        
    



