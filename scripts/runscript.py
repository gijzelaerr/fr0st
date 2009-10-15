""" This is a utility script that allows other scripts to be run as standalone
python programs or using fr0st.exe in the windows release.

Insert the following line at the top of your script:

from runscript import *

This will make it run in an execution environment identical to the one
provided in fr0st's scripting framework, minus the GUI hooks."""

import sys,os

if sys.path[0] == os.path.dirname(__file__):
    sys.path.append(sys.path[0])
    sys.path[0] = os.path.join(os.path.dirname(__file__),'..')

sys.dont_write_bytecode = True
from fr0stlib.fr0stlib import *

