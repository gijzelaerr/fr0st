class Interpolation(list):
   
    def __init__(self, keys, interval=50, flamename='frame', offset=0, curve='lin',
                 a=1.0, t=0.5, smooth=False, p_space='rect', c_space='hls'):

        nk = len(keys)
        nf = nk*interval
        
        curves = {}

        for i in xrange(nf):
            self.append(Flame())
            self[i].name = flamename + str(i + offset)
            
        #First frame is at 0

        for i in xrange(nk):
            #Equalize
            equalize_flame_attributes(keys[i-1], keys[i])
        
        #start frame attribs
        for name in keys[0].attributes:
            cps = []
            test = getattr(keys[0], name)
            if type(test) <> str and name not in 'size':
                for k in keys:
                    tmp = getattr(k,name)
                    if type(tmp) == list:
                        cps.append(tuple(tmp))
                    else:
                        cps.append(tmp)
                vector = interp(cps, interval, curve, a, t, smooth, True)
                for i in xrange(nf):
                    if type(vector[i]) == tuple:
                        setattr(self[i], name, list(vector[i]))
                    else:
                        setattr(self[i], name, vector[i])
            else:
                pass
        #done frame attribs
        #start xforms
        maxi = 0
        for k in keys:
            if len(k.xform)> maxi: maxi = len(k.xform)
        
        for i in xrange(maxi):
            #add blank xforms to all the dummies
            for f in self:
                f.add_xform()

            #coef interp
            cpsx = []
            cpsy = []
            cpso = []
            attrset = []
            for k in keys:
                if len(k.xform)<i+1:
                    cpsx.append((1, 0))
                    cpsy.append((0, 1))
                    cpso.append((0, 0))
                else:
                    a,d,b,e,c,f = k.xform[i].coefs
                    cpsx.append((a,d))
                    cpsy.append((b,e))
                    cpso.append((c,f))
                    attrset += set(attrset).union(k.xform[i].attributes)
            vx = interp(cpsx, interval, curve, a, t, smooth, True, p_space)
            vy = interp(cpsy, interval, curve, a, t, smooth, True, p_space)
            vo = interp(cpso, interval, curve, a, t, smooth, True, p_space)
            for j in xrange(nf):
                self[j].xform[i].coefs = [vx[j][0], vx[j][1], vy[j][0], vy[j][1], vo[j][0], vo[j][1]]
            
            #attribute interp
            for name in attrset:
                cps = []
                for k in keys:
                    if hasattr(k.xform[i], name): cps.append(getattr(k.xform[i], name))
                    else:                         cps.append(0)
                vector = interp(cps, interval, curve, a, t, smooth, True)
                for j in xrange(nf):
                    if name=='weight': vector[j] = clip(vector[j], 0.0000001, 10000)
                    setattr(self[j].xform[i], name, vector[j])

        #end xforms
        #start gradient
        for i in xrange(256):
            cps = []
            for k in keys:
                cps.append(k.gradient[i])
            vector = interp(cps, interval, curve, a, t, False, True, c_space)
            for j in xrange(nf):
                self[j].gradient[i] = vector[j]


def equalize_flame_attributes(flame1,flame2):
    """Make two flames have the same number of xforms and the same
    attributes. Also moves the final xform (if any) to flame.xform"""
    diff = len(flame1.xform) - len(flame2.xform)
    if diff < 0:
        for i in range(-diff):
            flame1.add_xform()
            flame1.xform[-1].symmetry = 1
    elif diff > 0:
        for i in range(diff):
            flame2.add_xform()
            flame2.xform[-1].symmetry = 1

    if flame1.final or flame2.final:
        for flame in flame1,flame2:
            flame.create_final()
            flame.xform.append(flame.final)
            flame.final = None

    # Size can be interpolated correctly, but it's pointless to
    # produce frames that can't be turned into an animation.
    flame1.size = flame2.size     

    for name in set(flame1.attributes).union(flame2.attributes):
        if not hasattr(flame2,name):
            val = getattr(flame1,name)
            _type = type(val)
            if _type is list or _type is tuple:
                setattr(flame2,name,[0 for i in val])
            elif _type is float:
                setattr(flame2,name,0.0)
            elif _type is str:
                delattr(flame1,name)
            else:
                raise TypeError, "flame.%s can't be %s" %(name,_type)
            
        elif not hasattr(flame1,name):
            val = getattr(flame2,name)
            _type = type(val)
            if _type is list or _type is tuple:
                setattr(flame1,[0 for i in val])
            elif _type is float:
                setattr(flame1,name,0.0)
            elif _type is str:
                delattr(flame2,name)
            else:
                raise TypeError, "flame.%s can't be %s" %(name,_type)

#------------------------------------------------
f1 = Flame(file='samples.flame',name='julia')
f2 = Flame(file='samples.flame',name='linear')
f3 = Flame(file='samples.flame',name='heart')
i = Interpolation([f1,f2,f3], smooth=True, curve='tanh')
while True:
    for f in i:
        SetActiveFlame(f)
        preview()
