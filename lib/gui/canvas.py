import itertools, numpy as N
from wx.lib.floatcanvas.FloatCanvas import FloatCanvas, GUIMode, DotGrid


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

    def __init__(self, parent):
        self.parent = parent
        FloatCanvas.__init__(self, parent,
                             size=(500,500),
                             ProjectionFun=None,
                             BackgroundColor="BLACK")

        # Create the reference triangle
        points = ((0,0),(1,0),(0,1))
        self.AddPolygon(points,
                        LineColor="Grey",
                        LineStyle="LongDash")
        map(lambda x,y,z: self.AddText(x,y,Position=z,Size=10,Color="Grey"),
            "OXY",points,("tr","tl","br"))
        
        self.MakeGrid()
        self.ZoomToBB()
        self.GUIMode = GUICustom(self)
        self.triangles = []


    def ShowFlame(self,flame):
        for t in self.triangles:
            self.RemoveObjects(itertools.chain((t,),t._text,t._circles))
        self.triangles = map(self.AddXform,flame.xform)

        # TODO: add post and finalxform.
        self.ZoomToBB()
        self.AdjustZoom()


    def AddXform(self,xform):
        color = self.colors[len(self.triangles) % len(self.colors)]
        points  = xform.coords
        triangle = self.AddPolygon(points,
                                   LineColor=color,
                                   LineStyle = "ShortDash")
        diameter = 6 / self.Scale
        circles = [self.AddCircle(i, Diameter=diameter, LineColor=color)
                   for i in points]
        text = map(lambda x,y: self.AddText(x,y,Size=10,Color=color),
                   "OXY",points)
        triangle._circles = circles
        triangle._text = text
        
        self.triangles.append(triangle)
        
        return triangle

      
    def MakeGrid(self):
        self.GridUnder = DotGrid(Spacing=(.1, .1),
                                 Size=200,
                                 Color=(100,100,100),
                                 Cross=True,
                                 CrossThickness=1)
        
    def AdjustZoom(self):
        """resets the grid and circle sizes, refreshes the canvas."""
        # Adjust Grid Spacing
        oldspacing = self.GridUnder.Spacing[0]
        newspacing = None
        scale = 25 / self.Scale  # this is an arbitrary constant.
        if scale > oldspacing:
            newspacing = oldspacing * 10
        elif scale < oldspacing / 10:
            newspacing = oldspacing / 10
        if newspacing:
            self.GridUnder.Spacing = N.array((newspacing,newspacing))

        # Adjust the circles at the triangle edges
        diameter = 6 / self.Scale
        map(lambda x: x.SetDiameter(diameter),
            itertools.chain(*(i._circles for i in self.triangles)))

        # Refresh canvas
        self._BackgroundDirty = True
        self.Draw()      

    # Currently not bound
    def OnZoomToFit(self,e):
        self.ZoomToBB()
        self.SetFocus() # Otherwise focus stays on Button.



class GUICustom(GUIMode.GUIMove):

    def OnLeftDown(self,e):
        # TODO: write event handlers for this
        e.Skip()

    def OnLeftUp(self,e):
        e.Skip()

    def OnRightDown(self,e):
##        self.Canvas.CaptureMouse() # Why was this here?
        self.StartMove = N.array(e.GetPosition())
        self.PrevMoveXY = (0,0)

    def OnRightUp(self,e):
        if self.StartMove is not None:
            self.EndMove = N.array(e.GetPosition())
            DiffMove = self.StartMove-self.EndMove
            if N.sum(DiffMove**2) > 16:
                self.Canvas.MoveImage(DiffMove, 'Pixel')
            self.StartMove = None

    def OnMove(self,e):
        
##        self.Canvas._RaiseMouseEvent(e,FloatCanvas.EVT_FC_MOTION)
        if e.Dragging() and e.RightIsDown() and self.StartMove is not None:
            self.EndMove = N.array(e.GetPosition())
##            self.MoveImage(e)
            DiffMove = self.StartMove-self.EndMove
            self.Canvas.MoveImage(DiffMove, 'Pixel')
            self.StartMove = self.EndMove
##            self.Canvas._BackgroundDirty = True
            self.Canvas.Draw()

        self.Canvas.SetFocus() # Makes Canvas take focus under windows.


    def OnWheel(self,e):
        self.Canvas.Zoom(1.25 if e.GetWheelRotation()>0 else 0.8)
        self.Canvas.AdjustZoom()

    def _get_MidMove(self):
        return self.StartMove

    def _set_MidMove(self,v):
        self.StartMove = v

    # Win uses MidMove, while Linux uses StartMove (WHY?). This makes the code
    # Compatible between both.
    MidMove = property(_get_MidMove,_set_MidMove)

