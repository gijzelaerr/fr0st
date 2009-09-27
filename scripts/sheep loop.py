

lst = []
name = flame.name + "%03d"
for i in range(120):
    for x in flame.xform:
        if x.animate:
            x.rotate(-3)
    flame.name = name % i
    lst.append(flame.copy())
    

set_flames("parameters/anim.flame", *lst)