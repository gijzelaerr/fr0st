from runscript import *


flame = Flame(file="samples.flame")

speedh = 0.089
speedv = 0.109
accelh = 0.004
accelv = 0.003
        
while 1:
    # Makes the gradient rotate slowly
    flame.pixels.insert(0,flame.pixels.pop())
    
    speedh += accelh
    speedv += accelv

    if abs(speedh) > 0.09: accelh = -accelh
    if abs(speedv) > 0.11: accelv = -accelv

    flame.xform[0].c += speedh
    flame.xform[0].f += speedv

    flame.xform[1].c -= speedh
    flame.xform[1].f -= speedv

    flame.xform[2].orbit(5,(0.3,0.3))
    
    record(flame.xform)
    display.render(flame)
