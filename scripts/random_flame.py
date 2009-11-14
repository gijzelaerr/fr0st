import random

from utils import calculate_colors, batch

    
def GenRandom(*args):
    f = Flame()
    for a in args:
        chance = a.get("chance", 1)
        if random.random() < chance:
            Xform.random(f, **a)
            
    f.reframe()
    calculate_colors(f)
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    return f


if __name__ == "__main__":
    randopt = [ { 'xv':range(1,6), 'n':2, 'xw':0},
                { 'xv':range(20,26), 'n':2, 'xw':0},
                { 'xv':range(6,9), 'n':1, 'fx':True, "chance":.5} ]
                
    lst = batch(GenRandom, 20, *randopt)
    save_flames("parameters/random_batch.flame", *lst)

