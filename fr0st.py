#Copyright (c) 2008 Vitor Bosshard
#This program licensed under the GPL. See license.txt for details.
#
#Tested under:
#Python 2.6.1
#Pygame 1.8.1.win32-py2.5
#-----------------------------------------------------------------

import os,sys

sys.path.append(os.getcwd())

if '.zip' in sys.path[0]: # Just for py2exe
    # Keep the zipfile on the path
    sys.path.append(sys.path[0])
    # Use abspath because an exact match is needed for comparisons
    newpath = os.path.join(sys.path[0],'..','..','scripts')
    sys.path[0] = os.path.abspath(newpath)
    # Py2exe won't find these imports otherwise.
    if False: import default,pygame,ctypes,Queue
else:
    sys.path[0] = os.path.join(sys.path[0],"scripts")
    
    
sys.dont_write_bytecode = True

if len(sys.argv) is 1:
    print('No script given as argument, loading default.py')
    sys.argv.append('default')

try:
    __import__(sys.argv[1])
except ImportError:
    raise ImportError, "Unable to load script %s" %modname
