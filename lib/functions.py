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
from display import Display

try:
    import pygame
    from pygame import (KMOD_ALT,KMOD_CAPS,KMOD_CTRL,KMOD_LALT,KMOD_LCTRL,
KMOD_LMETA,KMOD_LSHIFT,KMOD_META,KMOD_MODE,KMOD_NONE,KMOD_NUM,KMOD_RALT,
KMOD_RCTRL,KMOD_RMETA,KMOD_RSHIFT,KMOD_SHIFT,K_0,K_1,K_2,K_3,K_4,K_5,K_6,K_7,
K_8,K_9,K_AMPERSAND,K_ASTERISK,K_AT,K_BACKQUOTE,K_BACKSLASH,K_BACKSPACE,K_BREAK,
K_CAPSLOCK,K_CARET,K_CLEAR,K_COLON,K_COMMA,K_DELETE,K_DOLLAR,K_DOWN,K_END,
K_EQUALS,K_ESCAPE,K_EURO,K_EXCLAIM,K_F1,K_F10,K_F11,K_F12,K_F13,K_F14,K_F15,
K_F2,K_F3,K_F4,K_F5,K_F6,K_F7,K_F8,K_F9,K_FIRST,K_GREATER,K_HASH,K_HELP,K_HOME,
K_INSERT,K_KP0,K_KP1,K_KP2,K_KP3,K_KP4,K_KP5,K_KP6,K_KP7,K_KP8,K_KP9,
K_KP_DIVIDE,K_KP_ENTER,K_KP_EQUALS,K_KP_MINUS,K_KP_MULTIPLY,K_KP_PERIOD,
K_KP_PLUS,K_LALT,K_LAST,K_LCTRL,K_LEFT,K_LEFTBRACKET,K_LEFTPAREN,K_LESS,K_LMETA,
K_LSHIFT,K_LSUPER,K_MENU,K_MINUS,K_MODE,K_NUMLOCK,K_PAGEDOWN,K_PAGEUP,K_PAUSE,
K_PERIOD,K_PLUS,K_POWER,K_PRINT,K_QUESTION,K_QUOTE,K_QUOTEDBL,K_RALT,K_RCTRL,
K_RETURN,K_RIGHT,K_RIGHTBRACKET,K_RIGHTPAREN,K_RMETA,K_RSHIFT,K_RSUPER,
K_SCROLLOCK,K_SEMICOLON,K_SLASH,K_SPACE,K_SYSREQ,K_TAB,K_UNDERSCORE,K_UNKNOWN,
K_UP,K_a,K_b,K_c,K_d,K_e,K_f,K_g,K_h,K_i,K_j,K_k,K_l,K_m,K_n,K_o,K_p,K_q,K_r,
K_s,K_t,K_u,K_v,K_w,K_x,K_y,K_z)
except ImportError:
##    raise
    print("Warning: Couldn't import pygame.")
    # Ugly hack or clever trick? you decide!
    pygame = False

#-------------------------------------------------------------------------------

def polar(coord):
    return cmath.polar(complex(*coord))

def rect(r,phi):
    comp = cmath.rect(r,phi)
    return comp.real,comp.imag


def save_flame(filename,flame):
    save_flames(filename,flame)


def save_flames(filename,*flames):
    lst = [f.to_string() if isinstance(f,Flame) else f for f in flames]
    if os.path.exists(filename):
        shutil.copy(filename,os.path.splitext(filename)[0] + ".bak")
    f = open(filename,"w")
    f.write("""<flames name="Fr0st Batch">\n""")
    f.write("\n".join(lst))
    f.write("""</flames>""")
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

        
#------------------------------------------------------------------------------

display = Display()
keydown = display.keydown

try:
    display.init()
except:
    print("Warning: Can't initialize the display")
