""" TODO:

-Interpolate Gradient in another color space?

-Check if chaos interpolation works properly regarding added xforms

-Don't recalculate everything 100 times... or maybe do?
   -the first flame goes throug with pct = 0 ... pointless
   -the creation of temp_flame can be avoided, but produces som ugly floats
"""


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
               

def interpolate_coefs(xform1,xform2,temp_xform,pct):
    """Interpolates 2 xforms in the polar coordinate space.
    The x and y triangle points are interpolated in relation to the o point,
    and o in relation to (0,0)."""
    for coord in 'ad','be','cf':
        r1,phi1 = polar(map(xform1.__getattr__,coord))
        r2,phi2 = polar(map(xform2.__getattr__,coord))

        # Make sure the rotation is less than 180 degrees
        if   phi1-phi2 > pi: phi1 -= 2*pi
        elif phi2-phi1 > pi: phi2 -= 2*pi

        # When r is 0, phi needs to be set properly.
        if   not r1: phi1 = phi2
        elif not r2: phi2 = phi1

        newx,newy = rect((r1+(r2-r1)*pct,phi1+(phi2-phi1)*pct))
        
        # A 1e-7 value (occurs only with x) creates a pointless post xform.
        if abs(newx) < 0.000001: newx = 0
        
        setattr(temp_xform,coord[0],newx)
        setattr(temp_xform,coord[1],newy)

    
def interpolate(flame1,flame2,interval=50,flamename='frame',mode='linear',
                offset=0):
    if mode != 'linear':
        raise NotImplementedError

    buff = []

    # Make copies of the flames so the function has no side effects.
    flame1 = Flame(string=flame1.to_string())
    flame2 = Flame(string=flame2.to_string())
    
    equalize_flame_attributes(flame1,flame2)
    temp_flame = Flame(string=flame1.to_string())
    
    # On to the main loop
    for i in range(interval):
        pct = float(i)/interval

        # Interpolate flame attributes
        for name in temp_flame.attributes:
            val1 = getattr(flame1,name)
            val2 = getattr(flame2,name)
            _type = type(val1)
            if _type is list or _type is tuple:
                setattr(temp_flame,name,
                        [j1+(j2-j1)*pct for j1,j2 in zip(val1,val2)])
            elif _type is str:
                pass
            else:
                setattr(temp_flame,name,val1+(val2-val1)*pct)

        # Interpolate each xform
        for temp_xform,xform1,xform2 in zip(temp_flame.xform,flame1.xform,flame2.xform):
            
            interpolate_coefs(xform1,xform2,temp_xform,pct)
            interpolate_coefs(xform1.post,xform2.post,temp_xform.post,pct)
            
            temp_xform.chaos[:] = [j1+(j2-j1)*pct for j1,j2
                                   in zip(xform1.chaos,xform2.chaos)]

            for name in set(xform1.attributes).union(xform2.attributes):
                val1 = getattr(xform1,name)
                val2 = getattr(xform2,name)
                _type = type(val1)

                if _type is float or _type is int:
                    setattr(temp_xform,name,val1+(val2-val1)*pct)                       
                elif _type is str: # Catch plotmode
                    raise TypeError, '%s not supported' %(name)
                else:
                    raise TypeError, "xform.%s can't be %s" %(name,_type)
                
        # Finally, the gradient
        for j in range(256):
            r1,g1,b1 = flame1.gradient[j]
            r2,g2,b2 = flame2.gradient[j]
            temp_flame.gradient[j] = (r1+(r2-r1)*pct,
                                      g1+(g2-g1)*pct,
                                      b1+(b2-b1)*pct)

        temp_flame.name = '%s_%04d' %(flamename,i+offset)
        buff.append(temp_flame.to_string()) 
    
    return buff


# OJO, esto es una interfaz muy rigida.
def animate_file(oldfile,newfile,interval,last_to_first=False):
    """Animates all flames in a given file and saves the result as a .flame
    file."""

    flames = load_flames(oldfile)
    
    lst = interpolate_sequence(flames,interval,last_to_first)

    save_flames(newfile,*lst)


def interpolate_sequence(flames,interval,last_to_first=False):
    """Interpolates a list of flame objects."""

    if last_to_first:
        flames.append(Flame(string=flames[0].to_string()))
       
    result = []
    for i in range(len(flames)-1):
        segment = interpolate(flames[i],flames[i+1],
                              interval,offset=interval*i,flamename=flames[i].name[:-1])
        result.extend(segment)

    return result

    
#------------------------------------------------------------------------------
if name == '__main__':
    flame1 = Flame(file='test_interpolation.flame',name='1')
    flame2 = Flame(file='test_interpolation.flame',name='2')

    buff = interpolate(flame1,flame2,20,'test')

    save_flames(os.path.join('parameters','interpolate.flame'),*buff)
