#Copyright (c) 2008 Vitor Bosshard
#This program licensed under the GPL. See license.txt for details.
#
#Tested under:
#Python 2.6.1
#Pygame 1.8.1.win32-py2.5
#-----------------------------------------------------------------

# This code sets up the namespace in which fr0st scripts run

import os, sys, marshal, copy, random, cmath, shutil
from math import *
sys.dont_write_bytecode = False # Why is this line here?

import fr0stlib
from fr0stlib import Flame, Xform


#-------------------------------------------------------------------------------

def polar(coord):
##    return cmath.polar(complex(*coord)) # Use this once 2.6 is default
    l = sqrt(coord[0]**2 + coord[1]**2)
    theta = atan2(coord[1], coord[0]) * (180.0/pi)
    return l, theta   

def rect(r,phi):
##    comp = cmath.rect(r,phi)
##    return comp.real,comp.imag # Use this once 2.6 is default
    real = r * cos(phi*pi/180.0)
    imag = r * sin(phi*pi/180.0)
    return real, imag

def save_flame(filename,flame):
    save_flames(filename,flame)


def save_flames(filename,*flames):
    lst = [f.to_string() if isinstance(f,Flame) else f for f in flames]
    lst.insert(0, """<flames name="Fr0st Batch">\n""")
    lst.append("""</flames>""")
    head, ext = os.path.splitext(filename)
    if os.path.exists(filename) and ext == ".flame":
        shutil.copy(filename,head + ".bak")
    f = open(filename,"w")
    f.write("".join(lst))
    f.close()


def load_flames(filename,*args):
    """Reads a flame file and returns a list of flame objects, specified
    by index or name. If no flames are specified, returns all flames in the
    file, in order."""
    
    strings = Flame.load_file(filename)
    
    if not args:
        return [Flame(string=i) for i in strings]

    if all(map(lambda x: type(x) is int, args)):
           return [Flame(string=strings[key]) for key in args]

    flames = []
    re_name = re.compile(r'(?<= name=").*?(?=")')
    temp_names = map(lambda x: re_name.findall(x)[0], strings)

    for key in args:
        _type = type(key)
        if _type is str:
            try:
                key = temp_names.index(key)
            except ValueError:
                raise NameError, ' name "%s" not found in %s' %(key,filename)
        elif _type is not int:
            raise TypeError, "Expected flame index or name, got %s" %_type

        flames.append(Flame(string=strings[key]))
        
    return flames
