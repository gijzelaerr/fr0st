from wx.lib.floatcanvas.FloatCanvas import FloatCanvas, GUIMode, DotGrid
import numpy as N


class XformCanvas(FloatCanvas):
    colors = ["RED","YELLOW","GREEN"] # TODO: make this wrap around etc.

    def __init__(self, parent):
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
        xforms = flame.xform
        diff = len(self.triangles) - len(xforms)
        if diff < 0:
            map(self.AddXform, xforms[diff:])
        elif diff > 0:
            map(self.RemoveObject, self.triangles[-diff:])
            self.triangles = self.triangles[:-diff]

        for t,x in zip(self.triangles,xforms):
            t.Points = x.coords
            
        # TODO: add post and finalxform.
        
        self.ZoomToBB()


    def AddXform(self,xform):
        color = self.colors[len(self.triangles) % len(self.colors)]
        triangle = self.AddPolygon(xform.coords,
                                   LineColor=color)
                                   
        self.triangles.append(triangle)
        # TODO: add "OXY" text... maybe subclass FloatCanvas.Polygon.

        
    def MakeGrid(self):
        self.GridUnder = DotGrid(Spacing=(.1, .1),
                                 Size=200,
                                 Color=(100,100,100),
                                 Cross=True,
                                 CrossThickness=1)
        
    def AdjustGridSpacing(self):
        spacing = self.GridUnder.Spacing[0]
        newspacing = None
        # Scale is modified by an arbitrary constant that defines grid density.
        scale = 25 / self.Scale
        if scale > spacing:
            newspacing = spacing * 10
        elif scale < spacing / 10:
            newspacing = spacing / 10

        if newspacing:
            self.GridUnder.Spacing = N.array((newspacing,newspacing),
                                                    N.float)        

    # Currently not bound
    def OnZoomToFit(self,e):
        self.ZoomToBB()
        self.SetFocus() # Otherwise focus stays on Button.


class GUICustom(GUIMode.GUIMove):

    def __init__(self,canvas):
        self.Canvas = canvas
        self.StartMove = None
        self.PrevMoveXY = None

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
            StartMove = self.StartMove
            EndMove = N.array(e.GetPosition())
            DiffMove = StartMove-EndMove
            if N.sum(DiffMove**2) > 16:
                self.Canvas.MoveImage(DiffMove, 'Pixel')
            self.StartMove = None

    def OnMove(self,e):
##        self.Canvas._RaiseMouseEvent(e,FloatCanvas.EVT_FC_MOTION)
        if e.Dragging() and e.RightIsDown() and self.StartMove is not None:
            self.MoveImage(e)     


    def OnWheel(self,e):
        self.Canvas.Zoom(1.25 if e.GetWheelRotation()>0 else 0.8)
        self.Canvas.AdjustGridSpacing()
