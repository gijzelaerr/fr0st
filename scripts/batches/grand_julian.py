
def grand_julian():
    flame = Flame()
    flame.gradient.random(**config["Gradient-Settings"])

    # First xform: random variation for center goodness
    x = flame.add_xform()
    x.linear = 0
    x.blur = .4
    x.color_speed = 1

    # Make a julian xform with power = -2
    x = flame.add_xform()
    x.linear = 0
    x.julian = random.uniform(0.725, 1)
    x.julian_power = -2
    x.julian_dist = 1

    x.color = random.uniform(0, 1)
    x.color_speed = 0.25
    x.weight = 5
    x.c = 0.25 + random.uniform(0, 0.2)
    x.scale(0.25)
    x.post.scale(1.5)
    
    # Add additional julians
    for i in range(random.randint(2, 5)):
        x = flame.add_xform()
        x.linear = 0
        x.color = random.uniform(0, 1)
        x.c = random.uniform(-0.5, 0.5)
        x.scale(random.uniform(0.5, .8))
        
        x.julian_power = (2 ** random.randrange(2, 6))
        x.julian_dist = (random.randrange(-3, 4)
                         or random.uniform(-0.1, 0.1))
        x.julian = random.uniform(0.25, 4 - abs(x.julian_dist))

    return flame


def grand_julian_batch(nflames):
    lst = []
    name = "grand_julian%03d"
    for i in range(nflames):
        flame = grand_julian()
        flame.name = name % i
        lst.append(flame)
    return lst

if __name__ == "__main__":
    lst = grand_julian_batch(20)
    save_flames("parameters/grand_julians.flame", *lst)
    

