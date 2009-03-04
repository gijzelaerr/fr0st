from runscript import *

flame = Flame(file="samples.flame",name="julia")

active_xform = 0

while 1:

    if   K_LEFT in keydown:
        if active_xform > 0:
            active_xform -= 1
    elif K_RIGHT in keydown:
        if active_xform < len(flame.xform)-1:
            active_xform += 1
      
    mousepos = pygame.mouse.get_pos()
    flame.xform[active_xform].position = (mousepos[0]/320.0-1,
                                           -mousepos[1]/240.0+1)
    
    display.render(flame)
