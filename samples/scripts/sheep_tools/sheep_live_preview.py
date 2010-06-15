''' "It's aliiiiive!" he screamed, as the rotating sheep
mutated in realtime before his very eyes.'''

import time

from fr0stlib.gui._events import InMain
from fr0stlib.gui.constants import ID

def ScriptHack(func):
    # First, hack our way around some "limitations". I want to keep
    # all changes confined to this script, at least for now.
    # Don't do this at home.

    # Prevent normal updates to the preview image.
    global preview
    preview = _self.image.RenderPreview
    _self.image.RenderPreview = lambda *a, **k: None

    # Make the GUI believe the script is not running, so it'll
    # allow us to modify things on the canvas.
    _self.BlockGUI(False)
    enable = InMain(_self.Enable)
    enable(ID.RUN, False, editor=True)
    enable(ID.STOP, True, editor=True)

    # On to the actual script
    try:
        func()
    finally:
        # Undo the hackery. Stopping the script raises an
        # exception, so we need the finally clause.
        _self.image.RenderPreview = preview


def rotate_sheep(f, rot):
    for x in f.xform:
        if x.animate:
            x.rotate(rot)    

def main():
    """This is the actual script."""
    rot = 0
    while True:
        rot = (rot-3) % 360
        f = _self.flame.copy()
        rotate_sheep(f, rot)
        preview(f)
        time.sleep(0.05)


if __name__ == "__main__":
    ScriptHack(main)
