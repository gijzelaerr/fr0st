#from utils import calculate_colors

settings = dialog("Please enter the settings for this script:",
                  ("Number of spiral xforms", int, 6),
                  ("Rotation of each xform", float, 15),
                  ("Initial Scale", float, 0.9),
                  ("Scale reduction factor", float, 0.1),
                  ("Perform calculate_colors?", bool, True))

numspiral, rotation, initial, shrink, calc = settings


for i in range(1, numspiral + 1):
    xform = flame.add_xform()
    xform.scale(initial - i * shrink)
    xform.rotate(rotation * i)

#if calc:
    #calculate_colors(flame)
