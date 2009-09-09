import itertools, numpy as N, time, wx, sys, math
from functools import partial
from wx.lib.floatcanvas import FloatCanvas as FC
from wx.lib.floatcanvas.Utilities import BBox

from lib.decorators import Bind, BindEvents
from lib.fr0stlib import polar, rect, Xform
from lib import pyflam3
from lib.pyflam3 import Genome, c_double, RandomContext, flam3_xform_preview
from lib.gui.config import config


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
                                size=(300,300),
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
        self.triangles = []
        self.objects = []
        self.shadow = []

        self.MakeGrid()
        self.ZoomToBB(DrawFlag=False)
        self.AdjustZoom()

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

        for t in self.triangles:
            self.RemoveObjects(itertools.chain((t,),t._text,t._circles))
        self.triangles = []
        
        if self.preview is not None:
            self.RemoveObject(self.preview)
            self.preview = None
            
        for i in flame.iter_xforms():
            xf = self.AddXform(i, solid=i==self.parent.ActiveXform,
                               fill=i==self.SelectedXform)
            self.triangles.append(xf)
        
        # TODO: add post xforms.
##        for i in flame.iter_posts():
##            pass
                
        if rezoom:
            if self.preview is not None:
                # The preview spread is ignored, as it tends to zoom the flame
                # too far out.
                self.RemoveObject(self.preview)
                self.ZoomToBB(DrawFlag=False)
                self.AddObject(self.preview)
            else:
                self.ZoomToBB(DrawFlag=False)
            self.AdjustZoom()
        elif refresh:
            # This is an elif because AdjustZoom already forces a Draw.
            self.Draw()
    

    def AddXform(self, xform, solid=False, fill=False):
        color = ((255,255,255) if xform.isfinal()
                 else self.colors[xform.index%len(self.colors)])
        points  = xform.points
        triangle = self.AddPolygon(points,
                         LineColor=color,
                         FillColor=color,
                         FillStyle="BiDiagonalHatch" if fill else "Transparent",
                         LineStyle="Solid" if solid else self.style)

        diameter = self.circle_radius * 2
        circles = [self.AddCircle(i, Diameter=diameter, LineColor=color)
                   for i in points]
        text = map(lambda x,y: self.AddText(x,y,Size=10,Color=color),
                   "XYO",points)

        if solid:
            self._cornerpoints = self.GetCornerPoints(xform)
            corners = [self.AddLine(i, LineColor=color)
                       for i in self._cornerpoints]
            text.extend(corners)
            if config["Variation-Preview"]:
                self.preview = VarPreview(xform, Color=color)
                self.AddObject(self.preview)
            
        triangle._circles = circles
        triangle._text = text

        return triangle


    def GetCornerPoints(self, xform):
        """Calculate the lines making up the corners of the triangle."""
        a,d,b,e,c,f = xform.coefs

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
            itertools.chain(*(i._circles for i in self.triangles)))

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
            a,d,b,e,c,f = xform.coefs
            if polar((x - c, y - f))[0] < self.circle_radius:
                return (xform, partial(setattr, xform, "pos")
                               if config["Lock-Axes"]
                               else partial(setattr, xform, "o"))
            elif polar((x - a - c, y - d - f))[0] < self.circle_radius:
                return xform, partial(setattr, xform, "x")
            elif polar((x - b - c, y - e - f))[0] < self.circle_radius:
                return xform, partial(setattr, xform, "y")
        return None, None
    

    def CalcScale(self, points, h, v, hittest=False):
        """Returns the proportion by which the xform needs to be scaled to make
        the hypot pass through the point.
        If hittest is set to true, this func doubles as a hittest, and checks
        if the point is inside the line's hitbox."""

        xf = Xform(points=points)
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
            x,y,o = xform.points
            for points,func in (((x,y,o), 'scale'),
                                ((x,o,y), 'rotate_x'),
                                ((y,o,x), 'rotate_y')):
                if self.CalcScale(points, h, v, hittest=True):
                    return (points[:2], xform,
                            self.side_helper(xform, func, h,v))

        # TODO: detect the actual lines. Right now, it just checks a radius
        # from the middle point.
        radius = self.circle_radius * 3 # better too big than too small.
        for i,j,k in self._cornerpoints:
            if polar((h - j[0], v - j[1]))[0] < radius:
                xform = self.parent.ActiveXform
                return ((i,j,k), xform, self.side_helper(xform, 'rotate', h,v))

        return None, None, None

    
    def angle_helper(self, *points):
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
    

    def XformHitTest(self,x,y):
        """Checks if the given point is inside the area of the xform.
        This is done by testing if it falls inside the angles projected from
        at least 2 of its vertices."""
        for xform in self.IterXforms():
            a,d,b,e,c,f = xform.coefs
            if self.angle_helper((x-c, y-f), (a, d), (b, e)) and \
               self.angle_helper((x-a-c, y-d-f), (-a, -d), (b-a, e-d)):
                diff = x - xform.c, y - xform.f
                return xform, lambda coord: setattr(xform, "pos", coord-diff)
        return None, None


    # TODO: Currently not bound
    def OnZoomToFit(self,e):
        self.ZoomToBB(DrawFlag=False)
        self.AdjustZoom()
        self.SetFocus() # Otherwise focus stays on Button.


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
            t = self.AddXform(self.parent.ActiveXform)
            self.shadow.extend(itertools.chain((t,),t._text,t._circles))


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
        self.ReleaseMouse()
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
            if xform:
                self.SelectXform(xform)
                self.callback = cb

            elif self.SelectedXform is not None:
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

