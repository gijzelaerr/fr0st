from lib.functions import randrange2
from lib.fr0stlib import Flame, Xform

def GenRandomBatch(numrand,*a, **k):

    lst = []
    
    if len(a)==0:
        raise ValueError, "number of xform config specs must be > 0"

    if 'numbasic' in k and k['numbasic']>0 and len(a)>1:
        print "more than one xform config spec specified for basic mode, using only first one"

    for i in range(numrand):
        f = GenRandomFlame(*a, **k)
        f.name = "random_flame_%03d" % i
        lst.append(f)

    return lst    
    
def GenRandomFlame(*a,**k):

    if 'numbasic' in k:
        nb = k['numbasic']
        nxforms=randrange2(2,nb+1,int=int)
    else:
        nb=0
        nxforms = len(a)

    f = Flame()
        
    for i in range(nxforms):
        if (nb>0):
            Xform.random(f,col=float(i)/(nxforms-1),**a[0])        
        else:
            Xform.random(f,col=float(i)/(nxforms-1),**a[i])
    
    f.reframe()
    f.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))
    
    return f

if __name__ == "__main__":

    randopt = [ { 'xv':range(1,6), 'n':2, 'xw':0},
                { 'xv':range(20,26), 'n':2, 'xw':0},
                { 'xv':range(6,9), 'n':1, 'fx':.5} ]
                
    
    batchsize=20
    
    lst = GenRandomBatch(batchsize,*randopt,numbasic=3)
    save_flames("parameters/random_batch.flame",*lst)

