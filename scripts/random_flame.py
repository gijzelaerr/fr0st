


mxv = ( range(1,5), range(19,24) )
mn = (2,3)
mxw = (0,0)


lst = []
name = "random_test"

R = Flame()
R.name = name

for i in range(0, len(mxv)):
    xform = Xform.random(R,xv=mxv[i],n=mn[i],xw=mxw[i],col=i/(len(mxv)-1))

#calculate_colors(R)
R.reframe()
R.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))    
lst.append(R.copy())

set_flames("parameters/random_test.flame",*lst)


