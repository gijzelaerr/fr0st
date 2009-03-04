from runscript import *


print(
"""
The Playback Script
-------------------

Use the following controls for recording and reproduction:

r: start/stop recording
p: play recorded movements
c: clear recorded movements
"""
)



flame = Flame(file="samples.flame")

poshistory = []
posindex = 0
recording = False
playing = False

while 1:
                          
    if K_r in keydown: playing = False       ; recording = not recording
    if K_p in keydown: playing = not playing ; recording = False
    if K_c in keydown: playing = False       ; poshistory = []

    if playing:
        mousepos = poshistory[posindex]
        posindex += 1
        if posindex == len(poshistory):
            posindex = 0

    else:
        posindex = 0
        mousepos = pygame.mouse.get_pos()
        if recording:
            poshistory.append(mousepos)

    flame.xform[0].position = mousepos[0]/320.0-1, mousepos[1]/240.0-1
    display.render(flame)  

