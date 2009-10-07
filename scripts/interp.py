from runscript import *
from lib.utils import equalize_flame_attributes

class Interpolation(list):

    def __init__(self, keys, n=50, **kwargs):
        #Set defaults
        self.flamename = 'frame'
        self.offset = 0
        self.curve = 'lin'
        self.a = 1.0
        self.t = 0.5
        self.smooth = False
        self.loop = True
        kwargs['loop'] = True
        self.p_space = 'polar'
        self.c_space = 'rgb'

        #Get defaults from kwargs
        for key in kwargs:
            if key=='flamename': flamename=kwargs[key]
            elif key=='offset':  offset=kwargs[key]
            elif key=='curve':   curve=kwargs[key]
            elif key=='a':       a=kwargs[key]
            elif key=='t':       t=kwargs[key]
            elif key=='smooth':  smooth=kwargs[key]
            elif key=='p_space': p_space=kwargs[key]
            elif key=='c_space': c_space=kwargs[key]

        nk = len(keys)
        nf = nk * n

        tmp = []
        for i in xrange(nk):
            k1 = Flame(string=keys[i-1].to_string())
            k2 = Flame(string=keys[i].to_string())
            equalize_flame_attributes(k1, k2)
            tmp.append(k2)
        keys = tmp

        for i in range(nf):
            #Make new, empty flame
            self.append(Flame())
            self[i].name = self.flamename + str(self.offset+i)

            #Flame attrs
            interp_attrs = ['scale', 'rotate', 'brightness', 'gamma']
            for name, test in keys[0].iter_attributes():
                cps = []

                if name in interp_attrs:
                    for k in keys:
                        tmp = getattr(k,name)
                        if type(tmp) == list: cps.append(tuple(tmp))
                        else:                 cps.append(tmp)
                    val = interp(cps, n, i, **kwargs)
                    if type(val)==tuple: setattr(self[i], name, list(val))
                    else:                setattr(self[i], name, val)
                else:
                    pass
            #end flame attrs

            maxi = 0
            for k in keys:
                if len(k.xform)>maxi: maxi=len(k.xform)

            #Xform attrs
            for x in xrange(maxi):
                #Add xform
                self[i].add_xform()

                #coef interp
                cpsx = []
                cpsy = []
                cpso = []
                attrset = []
                for k in keys:
                    if len(k.xform)<x+1:
                        cpsx.append((1,0))
                        cpsy.append((0,1))
                        cpso.append((0,0))
                    else:
                        a,d,b,e,c,f = k.xform[x].coefs
                        cpsx.append((a,d))
                        cpsy.append((b,e))
                        cpso.append((c,f))
                        attrset += set(attrset).union(k.xform[x].attributes)
                vx = interp(cpsx, n, i, **kwargs)
                vy = interp(cpsy, n, i, **kwargs)
                vo = interp(cpso, n, i, **kwargs)
                self[i].xform[x].coefs = tuple(vx + vy + vo)

                #attribute intep
                for name in attrset:
                    cps = []
                    for k in keys:
                        if len(k.xform)>x and hasattr(k.xform[x], name):
                            cps.append(getattr(k.xform[x], name))
                        else:
                            cps.append(0)
                    val = interp(cps, n, i, **kwargs)
                    if name=='weight': val = clip(val, 0, 100)
                    setattr(self[i].xform[x], name, val)
            #end xforms

            #gradient
            for c, cps in enumerate(zip(*(key.gradient for key in keys))):
                val = interp(cps, n, i, **kwargs)
                self[i].gradient[c] = val
        #end xform
    #end init

"""
Erik's secret sauce added for better flava
"""
# TODO: this is currently not included... perhaps it should be put into
# equalize_flame_attributes in utils.
def get_pad(xform, target):
    HOLES = ['spherical', 'ngon', 'julian', 'juliascope', 'polar', 'wedge_sph', 'wedge_julia']

    target.add_xform()
    target.xform[-1] = copy.deepcopy(xform)
    t = target.xform[-1]
    t.coefs = [0.0,1.0,1.0,0.0,0.0,0.0]
    if len(set(t).intersection(HOLES)) > 0:
        #negative ident
        t.coefs = [-1.0,0.0,0.0,-1.0,0.0,0.0]
        t.linear = -1.0
    if 'rectangles' in t.attributes:
        t.rectangles = 1.0
        t.rectangles_x = 0.0
        t.rectangles_y = 0.0
    if 'rings2' in t.attributes:
        t.rings2 = 1.0
        t.rings2_val = 0.0
    if 'fan2' in t.attributes:
        t.fan2 = 1.0
        t.fan2_x = 0.0
        t.fan2_y = 0.0
    if 'blob' in t.attributes:
        t.blob = 1.0
        t.blob_low = 1.0
        t.blob_high = 1.0
        t.blob_waves = 1.0
    if 'perspective' in t.attributes:
        t.perspective = 1.0
        t.perspective_angle = 0.0
    if 'curl' in t.attributes:
        t.curl = 1.0
        t.curl_c1 = 0.0
        t.curl_c2 = 0.0
    if 'super_shape' in t.attributes:
        t.super_shape = 1.0
        t.super_shape_n1 = 2.0
        t.super_shape_n2 = 2.0
        t.super_shape_n3 = 2.0
        t.super_shape_rnd = 0.0
        t.super_shape_holes = 0.0
    if 'fan' in t.attributes:
        t.fan = 1.0
    if 'rings' in t.attributes:
        t.rings = 1.0
    t.weight = 0


if __name__ == '__main__':
    i = Interpolation(GetFlames(), smooth=True, curve='tanh')
    while True:
        for f in i:
            flame = f
            preview()
