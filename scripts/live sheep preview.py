''' "It's aliiiiive!" he screamed, as the rotating sheep
mutated in realtime before his very eyes.'''

import time
from threading import Lock

from lib.decorators import Locked

# First, hack our way around some "limitations". I want to keep
# all changes confined to this script, at least for now.
# Don't do this at home.

# Prevent normal updates to the preview window.
RenderPreview = self.image.RenderPreview
self.image.RenderPreview = lambda *a, **k: None

# Make the GUI believe the script is not running, so it'll
# allow us to modify things on the canvas.
self.scriptrunning = False

# Add a lock to make flame access threadsafe. This can only be
# achieved because self.flame is actually a property.
lock = Lock()
cls = self.__class__
_flameprop = cls.flame
cls.flame = property(Locked(lock)(cls.flame.fget), 
                     Locked(lock)(cls.flame.fset))

# On to the actual script
try:
    rot = 0
    while True:
        rot = (rot-5) % 360
        with lock:
            f = flame.copy()
        for x in f.xform:
            if x.symmetry <= 0:
                x.rotate(rot)
        RenderPreview(f)
        time.sleep(0.05)
finally:
    # Undo the hackery. Stopping the script raises an exception
    # in this thread, so we need the finally clause.
    self.image.RenderPreview = RenderPreview
    cls.flame = _flameprop
    RenderPreview()
