from utils import batch

def grand_julian():
    flame = Flame()
    flame.gradient.random(**config["Gradient-Settings"])

    # First xform: blur for center goodness
    flame.add_xform(linear=0, gaussian_blur=.4, color_speed=1)

    # Make a julian xform with power = -2
    x = flame.add_xform(linear=0, julian=random.uniform(0.725, 1),
                        julian_power=-2, julian_dist=1,
                        color=1, color_speed=.2, weight=5)
    x.c = 0.25 + random.uniform(0, 0.2)
    x.scale(0.25)
    x.post.scale(1.5)
    
    # Add additional julians
    for i in range(random.randint(2, 4)):
        x = flame.add_xform(linear=0, color=random.uniform(0, 1))
        x.c = random.uniform(-0.5, 0.5)
        x.scale(random.uniform(0.5, .8))

        x.julian_power = (2 ** random.randrange(2, 6))
        x.julian_dist = random.randrange(-3, 3)

        if not x.julian_dist:
            x.julian_dist = random.uniform(-0.1, 0.1)
            x.julian_power /= 2
        
        x.julian = random.uniform(0.25, 4 - abs(x.julian_dist))

    return flame

if __name__ == "__main__":
    lst = batch(grand_julian, 20)
    save_flames("grand_julian.flame", *lst)
    

