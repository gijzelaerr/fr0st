
# This script tests the response time for flam4 renders without interference
# from the GUI
while True:
    for x in flame.xform:
        if x.symmetry <= 0:
            x.rotate(-5)
    self.image.RenderPreview()
