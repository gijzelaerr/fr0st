from ..lib.gui.rendering import render

size = 256,192

buff = render(GetActiveFlame().to_string(),size,300)


self.image.UpdateBitmap(size,buff)