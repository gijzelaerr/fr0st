from runscript import *


flame = Flame(file='samples.flame',name='julia')


for i in range(1):
    flame.xform[0].rotate(15)
    flame_to_buffer(flame)
    
save_flame_buffer("anim.flame")

