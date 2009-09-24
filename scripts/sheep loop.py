

lst = []
name = flame.name + "%02d"
for i in range(72):
    for x in flame.xform:
        if x.animate:
            x.rotate(-5)
    flame.name = name % i
    lst.append(flame.copy())
    

set_flames("parameters/anim.flame", *lst)