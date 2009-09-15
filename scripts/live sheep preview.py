''' "It's aliiiiive!" he screamed, as the rotating sheep
mutated in realtime before his very eyes. This script may
cause segfaults, so use at your own risk.'''

import time

# First, some hackery to work around some "limitations". I want
# to keep all changes confined to this script, at least for now.
# Don't do this at home.
RenderPreview = self.image.RenderPreview
self.image.RenderPreview = lambda *a, **k: None

# Make the GUI believe the script is not running, so it'll
# allow us to modify things on the canvas.
self.scriptrunning = False

# On to the actual script
try:
    rot = 0
    while True:
        rot = (rot-5) % 360
        f = flame.copy()
        for x in f.xform:
            if x.symmetry <= 0:
                x.rotate(rot)
        RenderPreview(f)
        time.sleep(0.05)
finally:
    self.image.RenderPreview = RenderPreview
