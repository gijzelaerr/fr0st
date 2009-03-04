# This script overrides the normal iteration method with a custom defined one.
# It can be run on its own or imported into other scripts.

from runscript import *

oldxforms = [(0,0,0,0,0,0) for i in range(100)]

def iterate(flame):
    # Pretend to be a method using a "fake" self variable
    self = display

    # Create local variables for use in the inner loop  
    l_screen = self.screen
    zoom  = flame.scale * 2**flame.zoom / 100.0 * self.width     
    
    cam_x = self.width /2.0 - flame.center[0]* zoom
    cam_y = self.height/2.0 - flame.center[1]* zoom

    pixel = pygame.Surface((1,1))
    pixel.set_alpha(128)  
    totalweight = 0
    for xform in flame.xform: totalweight += xform.weight

    random.shuffle(samples)
    
    i = 0
    for k,xform in enumerate(flame.xform):       
        a, d, b, e, c, f  = xform.get_screen_coefs()
        a2,d2,b2,e2,c2,f2 = oldxforms[k]
        oldxforms[k] = a,d,b,e,c,f

        color = int((xform.color + self.iteration*0.001*128)%256)
        pixel.fill(flame.gradient[color])
        weight = int(xform.weight * self.quality / totalweight)

        ii = i+weight
        for j in range(i,ii):           
            #apply the affine transform to the sample.
            
            x,y = samples[j]
            x,y = ((a*x + b*y + c)*(j-i) + (a2*x + b2*y + c2)*(ii-j))/(weight), \
                  ((d*x + e*y + f)*(j-i) + (d2*x + e2*y + f2)*(ii-j))/(weight)
            samples[j] = x,y


            #draw transformed sample to screen.
            pos = round(x*zoom + cam_x), \
                  round(y*zoom + cam_y)
            try:l_screen.blit(pixel,pos)
            except: pass             
        i += weight

    self.iteration += 1
    return samples

def iterate_no_output(flame):
    #Create local variables for use in the inner loop
    
    totalweight = 0
    for xform in flame.xform: totalweight += xform.weight

    random.shuffle(samples)
    
    i = 0
    for xform in flame.xform:
        a,d,b,e,c,f = xform.get_screen_coefs()
        weight = int(xform.weight * display.quality / totalweight)

        for j in range(i,i+weight):           
            #apply the affine transform to the sample.
            x,y = samples[j]               
            x,y = a*x + b*y + c, d*x + e*y + f
            samples[j] = x,y              
        i += weight
    return samples
    
display.iterate = iterate
display.quality = 3000

if not flame:
    flame = Flame(file="samples.flame")

# Create a group of samples and get them into the bounds of the attractor.
samples = [(0,0) for i in range(display.quality)]
for i in range(20):
    iterate_no_output(flame)

if __name__ == "__main__":
    while 1:
        mousepos = pygame.mouse.get_pos()
        flame.xform[0].position = mousepos[0]/320.0-1, -mousepos[1]/240.0+1
        display.render(flame)
