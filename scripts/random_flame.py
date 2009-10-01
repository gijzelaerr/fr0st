
xv = ( range(1,5), range(19,24) )
n = (2,3)
xw = (0,0)



lst = []
name = "random_test"

R = Flame()
R.name = name

for i in range(0, len(xv)):

    xform = R.add_xform()
    xform.coefs = [random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1)]
    xform.linear=1.0

R.gradient.random(hue=(0, 1),saturation=(0, 1),value=(.25, 1),nodes=(4, 6))    
lst.append(R.copy())

set_flames("parameters/random_test.flame",*lst)


