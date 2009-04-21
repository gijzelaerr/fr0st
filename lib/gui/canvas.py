import itertools, numpy as N, time, wx, sys, math
from wx.lib.floatcanvas import FloatCanvas as FC
from wx.lib.floatcanvas.FloatCanvas import FloatCanvas, DotGrid

from decorators import Bind, BindEvents
from _events import EVT_CANVAS_REFRESH
from lib.functions import polar
from lib import pyflam3


class XformCanvas(FloatCanvas):
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
    
    @BindEvents
    def __init__(self, parent):
        self.parent = parent
        FloatCanvas.__init__(self, parent,
                             size=(400,400),
                             ProjectionFun=None,
                             BackgroundColor="BLACK")

        # Create the reference triangle
        points = ((0,0),(1,0),(0,1))
        self.AddPolygon(points,
                        LineColor="Grey",
                        LineStyle=self.style)
        map(lambda x,y,z: self.AddText(x,y,Position=z,Size=10,Color="Grey"),
            "OXY",points,("tr","tl","br"))


        # List that hold draw objects
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
        self.axes_locked = True
        self.HasChanged = False
        self.StartMove = None
        self.callback = None
        

    def ShowFlame(self, flame=None, rezoom=True, refresh=True):
        if flame is None:
            flame = self.parent.flame

        # Checks if the active xform is None or belongs to a previous flame.
        if (not self.parent.ActiveXform) or \
                self.parent.ActiveXform._parent != flame:
            self.parent.ActiveXform = flame.xform[0]
            
        for t in self.triangles:
            self.RemoveObjects(itertools.chain((t,),t._text,t._circles))
        self.triangles = []

        for i in flame.xform:
            self.triangles.append(self.AddXform(i, solid=i==self.parent.ActiveXform,
                                                fill=i==self.SelectedXform))
        
        if flame.final:
            self.triangles.append(self.AddXform(flame.final))
        
        self.triangles.append(self.AddXform(self.parent.ActiveXform, solid=True))

        # TODO: add post xforms.  
        
        if rezoom:
            self.ZoomToBB(DrawFlag=False)
            self.AdjustZoom()
        elif refresh:
            # This is an elif because AdjustZoom already forces a Draw.
            self.Draw()


    @Bind(EVT_CANVAS_REFRESH) # This is a custom event, not a FC one
    def OnCanvasRefresh(self, e):
        """Allows the script thread to ask the canvas to refresh."""
        self.ShowFlame(rezoom=False)


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
            
        triangle._circles = circles
        triangle._text = text

        return triangle

        
    def MakeGrid(self):
        self.GridUnder = DotGrid(Spacing=(.1, .1),
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


    def ActivateCallback(self,coords):
        if self.callback:
            self.callback(coords)
            self.ShowFlame(rezoom=False)
            self.parent.XformTabs.UpdateView()
            self.parent.image.RenderPreview()
            self.HasChanged = True


    def CalculateScale(self, xform, h, v):
        a,d,b,e,c,f = xform.coefs

        # The angle of the hypothenuse
        ratio = (e - d) / (a - b)
        diffv = (v - d - f) + (h - a - c) * ratio

        val = xform.d if abs(xform.d) > abs(xform.e) else xform.e
        return (diffv+val) / val


    def IterXforms(self):
        active = self.parent.ActiveXform
        lst = [i for i in self.parent.flame.xform if i != active]
        if active:
            lst.insert(0, active)
        if self.parent.flame.final:
            lst.append(self.parent.flame.final)
        return lst       


    def SideHitTest(self, h, v):

        for xform in self.IterXforms():
            a,d,b,e,c,f = xform.coefs

            if any((h < min(a, b) + c,
                    h > max(a, b) + c,
                    v < min(d, e) + f,
                    v > max(d, e) + f)):
                continue
            
            ratio = (e - d) / (a - b)
            diffx = (v - d - f) + (h - a - c) * ratio
            diffy = (v - e - f) + (h - b - c) * ratio

            height = diffx * diffy / math.sqrt(diffx**2 + diffy**2)
            if abs(height) < self.circle_radius:
                def callback(coord):
                    xform.scale(self.CalculateScale(xform,*coord))
                return (xform.x, xform.y), xform, callback

        return None, None, None
        

    
    def VertexHitTest(self,x,y):
        for xform in self.IterXforms():
            a,d,b,e,c,f = xform.coefs
            if polar((x - c, y - f))[0] < self.circle_radius:
                return (xform.o, xform, xform._set_position if self.axes_locked
                            else xform._set_o)
            elif polar((x - a - c, y - d - f))[0] < self.circle_radius:
                return xform.x, xform, xform._set_x
            elif polar((x - b - c, y - e - f))[0] < self.circle_radius:
                return xform.y, xform, xform._set_y
        return None, None, None
                

    def XformHitTest(self,x,y):            
        for xform in self.IterXforms():
            # check if the point is in an xform, by testing if it falls
            # inside the angles projected from at least 2 of its vertices
            a,d,b,e,c,f = xform.coefs
                        
            phiox = polar((a, d))[1]
            phioy = polar((b, e))[1]
            phiop = polar((x - c, y - f))[1]

            low,high = sorted((phiox,phioy))
            if high - low > 180:
                low, high = high-360, low
            if phiop > high:
                phiop -= 360
            if high > phiop > low:

                phixo = polar((-a, -d))[1]
                phixy = polar((b - a, e - d))[1]
                phixp = polar((x - a - c, y - d - f))[1]

                low, high = sorted((phixo,phixy))
                if high - low > 180:
                    low, high = high-360, low
                if phixp > high:
                    phixp -= 360
                        
                if high > phixp > low:
                    return xform


    # Currently not bound
    def OnZoomToFit(self,e):
        self.ZoomToBB(DrawFlag=False)
        self.AdjustZoom()
        self.SetFocus() # Otherwise focus stays on Button.


    @Bind(wx.EVT_ENTER_WINDOW)
    def OnEnter(self,e):
        self.CaptureMouse()

    @Bind(wx.EVT_LEAVE_WINDOW)
    def OnLeave(self,e):
        self.ReleaseMouse()
        

    @Bind(wx.EVT_IDLE)
    def OnIdle(self,e):
        if self._left_drag is not None:
            coords = self._left_drag
            self._left_drag = None
            self.ActivateCallback(coords)

        elif self._right_drag is not None:
            move = self._right_drag
            self._right_drag = None
            self.StartMove = self.EndMove
            self.MoveImage(move, 'Pixel')

        elif self._resize_pending != 1:
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
        self.ReleaseMouse()

        # EXPERIMENT!
        self.RemoveObjects(self.shadow)
        self.shadow = []
        self.Draw()
        
        if self.HasChanged:
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
        
        coords = self.PixelToWorld(e.GetPosition())
        
        if  e.RightIsDown() and e.Dragging() and self.StartMove is not None:
            self.EndMove = N.array(e.GetPosition())
            self._right_drag = self.StartMove - self.EndMove
            
        elif e.LeftIsDown() and e.Dragging():
            self._left_drag = coords
            
        else:
##            self.SetFocus() # Makes Canvas take focus under windows.

            # First, test for vertices
            vertex, xform, cb = self.VertexHitTest(*coords)
            if cb:
                self.SelectXform(xform)
                self.callback = cb
                return

            # Then, test for sides
            points, xform, cb = self.SideHitTest(*coords)
            if cb:
                self.SelectXform(xform, highlight=points)
                self.callback = cb
                return

            # Finally, test for area
            xform = self.XformHitTest(*coords)
            if xform:
                diff = coords - xform.o
                def callback(coord):
                    xform._set_position(coord-diff)
                self.callback = callback
                self.SelectXform(xform)

            else:
                self.SelectedXform = None
                self.ShowFlame(rezoom=False)
                self.callback = None


    def SelectXform(self, xform, highlight=None):
        self.SelectedXform = xform

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

