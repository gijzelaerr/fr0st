
ver, hor = dialog("Choose axis of Symmetry",
                  ("vertical", bool, True), 
                  ("horizontal", bool, True))

totalweight = sum(i.weight for i in flame.xform)

if hor:
    xform = flame.add_xform()
    xform.e *= -1
    xform.weight = totalweight
    xform.color_speed = 0
    xform.animate = 0

if ver:
    xform = flame.add_xform()
    xform.a *= -1
    xform.weight = totalweight * (1 + hor)
    xform.color_speed = 0
    xform.animate = 0
