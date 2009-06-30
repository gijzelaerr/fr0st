
while True:
    for x in flame.xform:
        if x.symmetry <= 0:
            x.rotate(-5)
    preview()
