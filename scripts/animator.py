from runscript import *
from interp import Interpolation

# HACK: put this in while John fixes his script.
from fr0stlib import utils
import interp
interp.equalize_flame_attributes = utils.equalize_flame_attributes

f1 = Flame(file='test_interpolation.flame',name='A')
f2 = Flame(file='test_interpolation.flame',name='B')


ilist = Interpolation([f1,f2], smooth=True, curve='tanh',
                       interval=35)

save_flames(os.path.join('parameters','interpolate.flame'),
            *(i.to_string() for i in ilist))
