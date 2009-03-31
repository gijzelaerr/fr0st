import itertools, numpy as N, time
from wx.lib.floatcanvas.FloatCanvas import FloatCanvas, DotGrid
from wx.lib.floatcanvas.GUIMode import GUIMove

from decorators import Bind, BindEvents
from _events import EVT_CANVAS_REFRESH


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

    @BindEvents
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

        self.triangles = []
        self.MakeGrid()
        self.ZoomToBB(DrawFlag=False)
        self.AdjustZoom()
        self.GUIMode = GUICustom(self)
        


    def ShowFlame(self,flame=None,rezoom=True,refresh=True):
        if flame is None:
            flame = self.parent.flame
        for t in self.triangles:
            self.RemoveObjects(itertools.chain((t,),t._text,t._circles))
        self.triangles = map(self.AddXform,flame.xform)
        
        if flame.final:
            self.AddXform(flame.final)
            
        # TODO: add post xforms.  

        if rezoom:
            self.ZoomToBB(DrawFlag=False)
            self.AdjustZoom()
        elif refresh:
            # This is an elif because AdjustZoom already forces a Draw.
            self.Draw()

    @Bind(EVT_CANVAS_REFRESH)
    def OnCanvasRefresh(self, e):
        """Allows the script thread to ask the canvas to refresh."""
        self.ShowFlame(rezoom=False)

    def AddXform(self,xform):
        if xform.isfinal():
            color = (255,255,255)
        else:
            color = self.colors[xform.index % len(self.colors)]
        points  = xform.coords
        triangle = self.AddPolygon(points,
                                   LineColor=color,
                                   LineStyle = "ShortDash")
        diameter = 8 / self.Scale
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
                                 Size=120,
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
        diameter = 8 / self.Scale
        map(lambda x: x.SetDiameter(diameter),
            itertools.chain(*(i._circles for i in self.triangles)))

        # Refresh canvas
        self._BackgroundDirty = True
        self.Draw()      

    # Currently not bound
    def OnZoomToFit(self,e):
        self.ZoomToBB(DrawFlag=False)
        self.AdjustZoom()
        self.SetFocus() # Otherwise focus stays on Button.



class GUICustom(GUIMove):
##    def __init__(self,canvas):
##        GUIMode.GUIMove.__init__(self,canvas)
##        self.callback = None

    def OnLeftDown(self,e):
        # TODO: select appropriate method based on cursor position, etc.
        self.callback = self.Canvas.parent.flame.xform[0]._set_position
        self._start_time = time.time()

    def OnLeftUp(self,e):
        self.callback = None
        self.Canvas.parent.TreePanel.TempSave()

    def OnRightDown(self,e):
##        self.Canvas.CaptureMouse() # Why was this here?
        self.StartMove = N.array(e.GetPosition())
        self.PrevMoveXY = (0,0)

    def OnRightUp(self,e):
        self.StartMove = None

    def OnMove(self,e):
        if  e.RightIsDown() and e.Dragging() and self.StartMove is not None:
            self.EndMove = N.array(e.GetPosition())
##            self.MoveImage(e)
            DiffMove = self.StartMove-self.EndMove
            self.Canvas.MoveImage(DiffMove, 'Pixel')
            self.StartMove = self.EndMove
            self.Canvas.Draw()
            
        elif e.LeftIsDown() and e.Dragging() and self.callback is not None:
            # HACK: we need to throttle the refresh rate of the canvas
            # to let through other events (WHY?)
            t = time.time()
            if t - self._start_time < .1:
                return
            self._start_time = t
            self.callback(self.Canvas.PixelToWorld(e.GetPosition()))
            self.Canvas.ShowFlame(rezoom=False)
            self.Canvas.parent.image.RenderPreview()
##            self.Canvas.Draw()

        else:
            # TODO: highlight triangle vertices, etc.
            
            # TODO: this is hacky and doesn't work well.
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

