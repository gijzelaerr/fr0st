##############################################################################
#  Fractal Fr0st - fr0st
#  https://launchpad.net/fr0st
#
#  Copyright (C) 2009 by Vitor Bosshard <algorias@gmail.com>
#
#  Fractal Fr0st is free software; you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this library; see the file COPYING.LIB.  If not, write to
#  the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 02111-1307, USA.
##############################################################################
import itertools, numpy as N, wx, sys
from functools import partial
from wx.lib.floatcanvas import FloatCanvas as FC
from wx.lib.floatcanvas.Utilities import BBox

from fr0stlib.decorators import Bind, BindEvents
from fr0stlib import polar, rect, Xform
from fr0stlib import pyflam3
from fr0stlib.pyflam3 import Genome, c_double, RandomContext, flam3_xform_preview
from fr0stlib.gui.config import config


def angle_helper(*points):
    """Given 3 vectors with the same origin, checks if the first falls
    between the other 2."""
    itr = (polar(i)[1] for i in points)
    vect = itr.next() # vector being checked
    low, high = sorted(itr) # the 2 triangle legs.
    if high - low > 180:
        low, high = high-360, low
    if vect > high:
        vect -= 360
    return high > vect > low


class VarPreview(FC.PointSet):

    def __init__(self, xform, Color):
        self.xform = xform
        lst = self.var_preview(xform, **config["Var-Preview-Settings"])
        FC.PointSet.__init__(self, lst, Color=Color)

    def var_preview(self, xform, range, numvals, depth):
        result = (c_double * (2* (2*numvals+1)**2))()
        genome = Genome.from_string(xform._parent.to_string(True))[0]
        index = xform.index
        if index is None:
            index = genome.final_xform_index
        flam3_xform_preview(genome, index, range, numvals, depth,
                            result, RandomContext())
        return [(x,-y) for x,y in zip(*[iter(result)]*2)]

##    def CalcBoundingBox(self):
##        # We don't want the BBox to be calculated from all points, as it messes
##        # with adjustzoom. Just triangle bounds are used, which causes a
##        # (slight) bug: when the triangle is dragged off-screen, the preview
##        # disappears, even if part of it would still be visible.
##        self.BoundingBox = BBox.fromPoints(self.xform.points)


class BaseCoefsTriangle(FC.Group):
    def __init__(self, parent, xform, points, coefs, color, solid, fill):
        
        self.xform = xform
        self.parent = parent
        self.points = points
        self.coefs = coefs
        self.color = color

        self.triangle = FC.Polygon(points,
                         LineColor=color,
                         FillColor=color,
                         FillStyle="BiDiagonalHatch" if fill else "Transparent",
                         LineStyle="Solid" if solid else parent.style)

        diameter = parent.circle_radius * 2

        circles = [FC.Circle(i, Diameter=diameter, LineColor=color) for i in points]

        text = map(lambda x,y: FC.Text(x,y,Size=10,Color=color), "XYO",points)

        self._circles = circles
        self._text = text

        FC.Group.__init__(self, [self.triangle] + circles + text)


    def VertexHitTest(self, x, y):
        a,d,b,e,c,f = self.coefs

        if polar((x - c, y - f))[0] < self.parent.circle_radius:
            return 'o'
        elif polar((x - a - c, y - d - f))[0] < self.parent.circle_radius:
            return 'x'
        elif polar((x - b - c, y - e - f))[0] < self.parent.circle_radius:
            return 'y'


class XFormTriangle(BaseCoefsTriangle):
    def __init__(self, parent, xform, color, solid=False, fill=False):
        BaseCoefsTriangle.__init__(self, parent, xform, xform.points, xform.coefs, color, solid, fill)

        if solid:
            parent._cornerpoints = parent.GetCornerPoints(xform)
            corners = [FC.Line(i, LineColor=color) for i in parent._cornerpoints]
            self._text.extend(corners)
            self.AddObjects(corners)


    def VertexHitTest(self, x, y):
        v = BaseCoefsTriangle.VertexHitTest(self, x, y)

        if v is None:
            return None, None
        elif v == 'o':
            return (self.xform, partial(setattr, self.xform, "pos")
                           if config["Lock-Axes"] else partial(setattr, self.xform, "o"))
        elif v == 'x':
            return self.xform, partial(setattr, self.xform, "x")

        elif v == 'y':
            return self.xform, partial(setattr, self.xform, "y")


class PostTriangle(BaseCoefsTriangle):
    def __init__(self, parent, xform, color, solid=False, fill=False):
        BaseCoefsTriangle.__init__(self, parent, xform, xform.post.points, xform.post.coefs, color, solid, fill)

        if solid:
            parent._post_cornerpoints = parent.GetCornerPoints(xform, True)
            corners = [FC.Line(i, LineColor=color) for i in parent._post_cornerpoints]
            self._text.extend(corners)
            self.AddObjects(corners)


    def VertexHitTest(self, x, y):
        v = BaseCoefsTriangle.VertexHitTest(self, x, y)

        if v is None:
            return None, None
        elif v == 'o':
            return (self.xform, partial(setattr, self.xform.post, "pos")
                           if config["Lock-Axes"] else partial(setattr, self.xform.post, "o"))
        elif v == 'x':
            return self.xform, partial(setattr, self.xform.post, "x")

        elif v == 'y':
            return self.xform, partial(setattr, self.xform.post, "y")


class XformCanvas(FC.FloatCanvas):
    colors = [( 255,   0,   0), # red
              ( 255, 255,   0), # yellow
              (   0, 255,   0), # green
              (   0, 255, 255), # light blue
              (   0,   0, 255), # dark blue
              ( 255,   0, 255), # purple
              ( 255, 127,   0), # orange
              ( 255,   0, 127)  # another purplish one
              ] # TODO: extend the color list.

    style = "ShortDash" if "linux" in sys.platform else "Dot"
    preview = None

    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        FC.FloatCanvas.__init__(self, parent,
                                size=(300,300), # HACK: This needs to be here.
                                ProjectionFun=None,
                                BackgroundColor="BLACK")

        # Create the reference triangle
        points = ((0,0),(1,0),(0,1))
        self.AddPolygon(points,
                        LineColor="Grey",
                        LineStyle=self.style)
        map(lambda x,y,z: self.AddText(x,y,Position=z,Size=10,Color="Grey"),
            "OXY",points,("tr","tl","br"))


        # Lists that hold draw objects
        self.xform_groups = []
        self.post_groups = []
        self.objects = []
        self.shadow = []
        self.edit_post = False

        self.MakeGrid()

        # These are used in the OnIdle Method
        self._right_drag = None
        self._left_drag = None
        self._resize_pending = 1

        # These mark different states of the canvas
        self.parent.ActiveXform = None
        self.SelectedXform = None
        self._highlight = None
        self.HasChanged = False
        self.StartMove = None
        self.callback = None

    def ShowFlame(self, flame=None, rezoom=True, refresh=True):
        if flame is None:
            flame = self.parent.flame

        self.RemoveObjects(self.xform_groups)
        self.xform_groups = []

        self.RemoveObjects(self.post_groups)
        self.post_groups = []

        if self.preview is not None:
            self.RemoveObject(self.preview)
            self.preview = None

        for i in flame.iter_xforms():
            xf = self.AddXform(i, solid=i==self.parent.ActiveXform,
                               fill=i==self.SelectedXform)
            self.xform_groups.append(xf)

            p = self.AddXform(i, solid=i==self.parent.ActiveXform,
                               fill=i==self.SelectedXform, post=True)
            self.post_groups.append(p)
                
            xf.Visible = not config['Edit-Post-Xform']
            p.Visible = config['Edit-Post-Xform']


        if rezoom:
            self.ZoomToFit()
        elif refresh:
            # This is an elif because AdjustZoom already forces a Draw.
            self.Draw()


    def AddXform(self, xform, solid=False, fill=False, post=False):
        color = ((255,255,255) if xform.isfinal()
                 else self.colors[xform.index%len(self.colors)])

        if post:
            t = PostTriangle(self, xform, color, solid, fill)
        else:
            t = XFormTriangle(self, xform, color, solid, fill)
            if solid and config["Variation-Preview"]:
                self.preview = VarPreview(xform, Color=color)
                self.AddObject(self.preview)            
        self.AddObject(t)

        return t

    def GetCornerPoints(self, xform, post=False):
        """Calculate the lines making up the corners of the triangle."""
        a,d,b,e,c,f = xform.coefs if not post else xform.post.coefs

        # Get the 4 corner points
        p1 = c + a + b, f + d + e
        p2 = c + a - b, f + d - e
        p3 = c - a + b, f - d + e
        p4 = c - a - b, f - d - e

        # define towards which other corners the corner lines will point.
        # (p1, p4) and (p2, p3) are opposing corners.
        combinations = ((p1,p2,p3),
                        (p2,p1,p4),
                        (p3,p1,p4),
                        (p4,p2,p3))

        # Make the length of the corner lines 1/10th of the distance to the
        # respective corner. The lists of points returned will be drawn as
        # multilines.
        return [((x1+(x2-x1)/10, y1+(y2-y1)/10),
                 (x1, y1),
                 (x1+(x3-x1)/10, y1+(y3-y1)/10))
                for (x1,y1),(x2,y2),(x3,y3) in combinations]


    def MakeGrid(self):
        self.GridUnder = FC.DotGrid(Spacing=(.1, .1),
                                    Size=150,
                                    Color=(100,100,100),
                                    Cross=True,
                                    CrossThickness=1)


    def AdjustZoom(self):
        """resets the grid and circle sizes, refreshes the canvas."""
        # Adjust Grid Spacing
        oldspacing = self.GridUnder.Spacing[0]
        newspacing = None
        scale = 25 / self.Scale  # this is an arbitrary constant.
        from math import log
        if scale > oldspacing:
            newspacing = oldspacing * 10**int(log(scale/oldspacing,10)+1)
        elif scale < oldspacing / 10:
            newspacing = oldspacing / 10
        if newspacing:
            self.GridUnder.Spacing = N.array((newspacing,newspacing))

        # Adjust the circles at the triangle edges
        diameter = self.circle_radius * 2
        map(lambda x: x.SetDiameter(diameter),
            itertools.chain(*(i._circles for i in self.xform_groups)))

        map(lambda x: x.SetDiameter(diameter),
            itertools.chain(*(i._circles for i in self.post_groups)))

        # Refresh canvas
        self._BackgroundDirty = True
        self.Draw()


    def IterXforms(self):
        active = self.parent.ActiveXform
        lst = [i for i in self.parent.flame.xform if i != active]
        if active:
            lst.insert(0, active)
        if self.parent.flame.final:
            lst.append(self.parent.flame.final)
        return lst


    def IterXformGroups(self):
        lst = []

        for xform_group in self.xform_groups:
            if xform_group.xform == self.parent.ActiveXform:
                lst.insert(0, xform_group)
            else:
                lst.append(xform_group)

        #TODO: Handle final xform as xformgroup
        #if self.parent.flame.final:
        #    lst.append(self.parent.flame.final)

        return lst


    def ActivateCallback(self,coords):
        if self.callback:
            self.callback(coords)
            self.HasChanged = True
            self.ShowFlame(rezoom=False)
            # Only update Xform, not all 4 tabs. makes updates somewhat faster.
            self.parent.XformTabs.Xform.UpdateView()
            self.parent.image.RenderPreview()


    def VertexHitTest(self,x,y):
        """Checks if the given point is on top of a vertex."""

        for xform in self.IterXforms():
            xf = xform if not config['Edit-Post-Xform'] else xform.post
            a,d,b,e,c,f = xf.coefs

            if polar((x - c, y - f))[0] < self.circle_radius:
                return (xform, partial(setattr, xf, "pos") if config["Lock-Axes"] else partial(setattr, xf, "o"))
            elif polar((x - a - c, y - d - f))[0] < self.circle_radius:
                return xform, partial(setattr, xf, "x")
            elif polar((x - b - c, y - e - f))[0] < self.circle_radius:
                return xform, partial(setattr, xf, "y")

        return None, None



    def CalcScale(self, points, h, v, hittest=False):
        """Returns the proportion by which the xform needs to be scaled to make
        the hypot pass through the point.
        If hittest is set to true, this func doubles as a hittest, and checks
        if the point is inside the line's hitbox."""

        xf = Xform(None, points=points)
        a,d,b,e,c,f = xf.coefs

        # Get angle of the hypothenuse
        angle = polar(((b-a), (e-d)))[1]

        # create a rotated triangle and (c,f)->(h,v) vector. This way, the
        # hypothenuse is guaranteed to be horizontal, which makes everything
        # easier.
        xf.rotate(-angle)
        l, theta = polar(((h-c), (v-f)))
        width,height = rect((l, theta - angle))

        # return the result.
        # Note that xf.d and xf.e are guaranteed to be equal.
        if hittest:
            return xf.a < width < xf.b and \
                   abs(height - xf.d) < self.circle_radius
        return height / xf.d


    def side_helper(self, xform, funcname, h, v):
        """Takes the result of SideHitTest and builds a proper callback."""
        if funcname == 'scale':
            def cb((h,v)):
                return xform.scale(self.CalcScale(xform.points, h, v))
            return cb

        if funcname == "rotate" or config["Lock-Axes"]:
            pivot = (0,0) if config["World-Pivot"] else xform.o
            func = partial(xform.rotate, pivot=pivot)
        else:
            pivot = xform.o
            func = getattr(xform, funcname)

        def cb((h, v)):
            angle = polar((h - pivot[0], v - pivot[1]))[1]
            func(angle - cb.prev_angle)
            cb.prev_angle = angle
        cb.prev_angle = polar((h - pivot[0], v - pivot[1]))[1]
        return cb


    def SideHitTest(self, h, v):
        """Checks if the given point is near one of the triangle sides
        or corners."""
        for xform in self.IterXforms():
            xf = xform if not config['Edit-Post-Xform'] else xform.post
            x,y,o = xf.points
            for points,func in (((x,y,o), 'scale'),
                                ((x,o,y), 'rotate_x'),
                                ((y,o,x), 'rotate_y')):
                if self.CalcScale(points, h, v, hittest=True):
                    return (points[:2], xform,
                            self.side_helper(xf, func, h,v))

        # TODO: detect the actual lines. Right now, it just checks a radius
        # from the middle point.
        radius = self.circle_radius * 3 # better too big than too small.
        for i,j,k in (self._cornerpoints if not config['Edit-Post-Xform'] else self._post_cornerpoints):
            if polar((h - j[0], v - j[1]))[0] < radius:
                xform = self.parent.ActiveXform
                return ((i,j,k), xform, self.side_helper(xform if not config['Edit-Post-Xform'] else xform.post, 'rotate', h,v))

        return None, None, None


    def XformHitTest(self,x,y):
        """Checks if the given point is inside the area of the xform.
        This is done by testing if it falls inside the angles projected from
        at least 2 of its vertices."""

        for xform in self.IterXforms():
            xf = xform if not config['Edit-Post-Xform'] else xform.post
            a,d,b,e,c,f = xf.coefs

            if angle_helper((x-c, y-f), (a, d), (b, e)) and \
               angle_helper((x-a-c, y-d-f), (-a, -d), (b-a, e-d)):
                diff = x - c, y - f
                return xform, lambda coord: setattr(xf, "pos", coord-diff)

        return None, None


    def ZoomToFit(self):
        if self.preview is not None:
            # The preview spread is ignored, as it tends to zoom the flame
            # too far out.
            self.RemoveObject(self.preview)
            self.ZoomToBB(DrawFlag=False)
            self.AddObject(self.preview)
        else:
            self.ZoomToBB(DrawFlag=False)
        self.AdjustZoom()


    @Bind(wx.EVT_ENTER_WINDOW)
    def OnEnter(self,e):
##        self.CaptureMouse()
        pass

    @Bind(wx.EVT_LEAVE_WINDOW)
    def OnLeave(self,e):
##        self.ReleaseMouse()
        pass


    @Bind(wx.EVT_IDLE)
    def OnIdle(self,e):
        if self._left_drag is not None:
            coords = self._left_drag
            self._left_drag = None
            self.ActivateCallback(coords)

        if self._right_drag is not None:
            move = self._right_drag
            self._right_drag = None
            self.StartMove = self.EndMove
            self.MoveImage(move, 'Pixel')

        if self._resize_pending != 1:
            # Don't use self.Zoom because it redraws unconditionally.
            self.Scale *= self._resize_pending
            self._resize_pending = 1
            self.SetToNewScale(DrawFlag=False)
            self.RemoveObjects(self.objects)
            self.AdjustZoom()
            self.AddObjects(self.objects)


    @Bind(FC.EVT_MOUSEWHEEL)
    def OnWheel(self,e):
        self._resize_pending *= 1.25 if e.GetWheelRotation()>0 else 0.8


    @Bind(FC.EVT_LEFT_DOWN)
    def OnLeftDown(self,e):
        self.CaptureMouse()
        if self.SelectedXform:
            self.parent.ActiveXform = self.SelectedXform
            self.ShowFlame(rezoom=False)
            self.parent.XformTabs.UpdateView()

            # EXPERIMENT!
            if config['Edit-Post-Xform']:
                t = self.AddXform(self.parent.ActiveXform, post=True)
            else:
                t = self.AddXform(self.parent.ActiveXform)

            self.shadow.extend((t,))


    @Bind(FC.EVT_LEFT_UP)
    def OnLeftUp(self,e):
        # This release mouse causes a bug under windows.
##        self.ReleaseMouse()

        # EXPERIMENT!
        self.RemoveObjects(self.shadow)
        self.shadow = []

        if self.HasChanged:
            # Heisenbug, thou art no more! Since TempSave triggers a redraw,
            # It was possible that an idle event was still pending afterwards,
            # which could cause a different xform to change its position in
            # a bizarre way. Calling OnIdle fixes this.
            self.OnIdle(None)
            self.HasChanged = False
            self.parent.TreePanel.TempSave()


    @Bind(FC.EVT_RIGHT_DOWN)
    def OnRightDown(self,e):
        self.CaptureMouse()
        self.StartMove = N.array(e.GetPosition())
        self.PrevMoveXY = (0,0)


    @Bind(FC.EVT_RIGHT_UP)
    def OnRightUp(self,e):
        if self.HasCapture():
            self.ReleaseMouse()

        self.StartMove = None


    @Bind(wx.EVT_MOUSE_CAPTURE_LOST)
    def OnLostMouseCapture(self, e):
        self.StartMove = None


    @Bind(FC.EVT_MOTION)
    def OnMove(self,e):
        self.RemoveObjects(self.objects)
        self.objects = []

        if  e.RightIsDown() and e.Dragging() and self.StartMove is not None:
            self.EndMove = N.array(e.GetPosition())
            self._right_drag = self.StartMove - self.EndMove

        elif self.parent.scriptrunning:
            # Disable everything except canvas dragging.
            return

        elif e.LeftIsDown() and e.Dragging():
            self._left_drag = e.Coords

        else:
            # TODO: maybe uncomment this SetFocus, but activate it only
            # when main frame has focus.
##            self.SetFocus() # Makes Canvas take focus under windows.


            # First, test for vertices
            xform, cb = self.VertexHitTest(*e.Coords)
            if cb:
                self.SelectXform(xform)
                self.callback = cb
                return

            # Then, test for sides
            line, xform, cb = self.SideHitTest(*e.Coords)
            if cb:
                self.SelectXform(xform, highlight=line)
                self.callback = cb
                return

            # Finally, test for area

            xform, cb = self.XformHitTest(*e.Coords)

            if cb:
                self.SelectXform(xform)
                self.callback = cb
                return

            if self.SelectedXform is not None:
                # Showflame is called here because SelectXform is not.
                self.SelectedXform = None
                self.callback = None
                self.ShowFlame(rezoom=False)


    def SelectXform(self, xform, highlight=None):
        if self.SelectedXform == xform and self._highlight == highlight:
            return

        self.SelectedXform = xform
        self._highlight = highlight

        varlist = [i for i in pyflam3.variation_list if getattr(xform,i)]
        color = ((255,255,255) if xform.isfinal()
                 else self.colors[xform.index%len(self.colors)])
        hor, ver = self.GetSize()
        hor -= 5
        ver -= 5

        for i in reversed(varlist):
            ver -= 12
            self.objects.append(self.AddText(i, self.PixelToWorld((hor,ver)),
                                Size = 8, Position = "tr", Color=color))

        if highlight:
            self.objects.append(self.AddLine(highlight, LineColor=color,
                                             LineWidth=2))
        self.ShowFlame(rezoom=False)


    def _get_MidMove(self):
        return self.StartMove

    def _set_MidMove(self,v):
        self.StartMove = v

    # Win uses MidMove, while Linux uses StartMove (WHY?). This makes the code
    # Compatible between both.
    MidMove = property(_get_MidMove,_set_MidMove)


    def _get_circle_radius(self):
        return 5 / self.Scale

    circle_radius = property(_get_circle_radius)

