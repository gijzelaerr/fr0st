
update_flame = False

while True:
    for x in flame.xform:
        if x.animate:
            x.rotate(-3)
    preview()
