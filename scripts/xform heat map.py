"""
Xform heat map.

This script is useful to see which xform is responsible for each
part of the image. Colors are the same as the triangles on the
canvas.
"""

from fr0stlib.gui.canvas import XformCanvas

# Divide gradient into 8 blocks.
for i, color in enumerate(XformCanvas.colors):
    flame.gradient[i*32:i*32+32] = [color] * 32

# Set xform colors so they fall into their respective blocks.
for x in flame.xform:
    x.color_speed = 1
    x.color = 1/16. + x.index % 8 / 8.


