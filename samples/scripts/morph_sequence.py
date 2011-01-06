from fr0stlib.render import to_string
from fr0stlib.pyflam3 import Genome, byref, flam3_interpolate

from utils import animation_preview


def interpolate(flames):
    s = "<flames>%s</flames>" % "".join(map(to_string, flames))
    genomes, ngenomes = Genome.from_string(s)
    
    target = Genome()
    for i in range(int(flames[0].time), int(flames[-1].time + 1)):
        flam3_interpolate(genomes, ngenomes, i, 0, byref(target))
        flame = Flame(target.to_string())
        flame.name = "morphed_%04d" % i
        yield flame
        

def getinput():
    flames = get_flames()
    res = dialog("Choose settings.\n\n(Keyframe interval = 0 "
                 "uses the time attribute of each flame instead "
                 "of a fixed interval)",
                 ("First flame", flames),
                 ("Last flame", flames, len(flames) - 1),
                 ("keyframe interval", int, 0),
                 ("wrap around", bool),
                 ("preview only", bool, True))
    first, last, interval, wrap, preview = res
    flames = flames[flames.index(first):flames.index(last)+1]
    if len(flames) < 2:
        raise ValueError("Need to select at least 2 flames")
    return flames, interval, wrap, preview


update_flame = False

flames, interval, wrap, preview_only = getinput()


if wrap:
    if not interval:
        raise ValueError("Wrap is only allowed when keyframe "
                         "interval is not 0")
    flames.append(flames[0].copy())

if interval:
    for i, flame in enumerate(flames):
        flame.time = i * interval
else:
    flames = sorted(flames, key=lambda f: f.time)

if len(set(f.time for f in flames)) != len(flames):
    raise ValueError("2 or more flames have the same time value.")

flame_gen = interpolate(flames)
if preview_only:
    animation_preview(flame_gen)
else:
    save_flames("parameters/morph_sequence.flame", *tuple(flame_gen),
                confirm=False)
