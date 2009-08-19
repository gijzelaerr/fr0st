
ver, hor = dialog("Symmetry", "Choose axis of Symmetry",
                  ("vertical", True), 
                  ("horizontal", True))

totalweight = sum(i.weight for i in flame.xform)

if hor:
    xform = flame.add_xform()
    xform.e *= -1
    xform.weight = totalweight
    xform.color = 1
    xform.symmetry = 1

if ver:
    xform = flame.add_xform()
    xform.a *= -1
    xform.weight = totalweight * (1 + hor)
    xform.color = 1
    xform.symmetry = 1   
