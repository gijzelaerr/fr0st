
def sheep_loop(flame, nframes):
    name = flame.name + " %03d"
    lst = []
    for i in range(nframes):
        for x in flame.xform:
            if x.animate:
                x.rotate(-360./nframes)
        flame.name = name % i
        lst.append(flame.copy())
    return lst


if __name__ == '__main__':
    save_flames("parameters/sheep_loop.flame", *sheep_loop(flame, 120),
                confirm=False)
