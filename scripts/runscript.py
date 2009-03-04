import sys,os

sys.dont_write_bytecode = True

if sys.path[0] == os.path.dirname(__file__):
    sys.path.append(sys.path[0])
    sys.path[0] = os.path.join(os.path.dirname(__file__),'..')
    sys.dont_write_bytecode = False
    from lib.functions import *

