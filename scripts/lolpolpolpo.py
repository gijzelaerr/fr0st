from random_flame import GenRandomBatch
#from lib.functions import randrange2
import random

# Customize here for awesomeness
special_vars = (2,3,15,17,23,32,55,59,66,80)

# Lolpolpolpo, by Coppercat
randopt = { 'xv':(0,), 'n':1, 'xw':0}
nflames = 5
lst = GenRandomBatch(nflames, randopt, numbasic=5)

k=0

for f in lst:

    # Normalize weights of xforms in this flame
    # and divide them all by 2
    tw=0
    for x in f.iter_xforms():
        if not x.isfinal():
            tw += x.weight

    tw *= 2.0

    for x in f.iter_xforms():
        if not x.isfinal():
            x.weight /= tw

    # Choose a random xform.  Delete it and create a new one
    # with the same weight using variations in special_vars
    # choosing 3 of them
    delx = randrange2(0,len(f.xform),int=int)
    delxw = f.xform[delx].weight
    delcol = f.xform[delx].color
    
    f.xform[delx].delete()

    Xform.random(f, xv=special_vars, n=3, xw=delxw, col=delcol)

    # Add one more all-linear xform with weight 0.5
    # with the magic rotation & offset
    lastx = f.add_xform()

    lastx.rotate(random.uniform(0,10) + 15)
    lastx.c = random.uniform(-0.5, 0.5)
    lastx.f = random.uniform(-0.5, 0.5)
    lastx.weight = 0.5
    lastx.color_speed = 0

    f.reframe()
    f.name = "lolpolpolpo_%03d" % k
    k+=1


set_flames("parameters/random_batch.flame",*lst)
    



