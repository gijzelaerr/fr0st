

def sheep_loop(flame, nframes):
    name = flame.name.replace(" ", "") + "%03d"
    lst = []
    for i in range(nframes):
        for x in flame.xform:
            if x.animate:
                x.rotate(-360./nframes)
        flame.name = name % i
        lst.append(flame.copy())
    return lst
