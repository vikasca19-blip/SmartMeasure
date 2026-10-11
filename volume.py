import math


# ---------------------------------------
# Cuboid
# ---------------------------------------

def cuboid_volume(width, height, depth):

    return round(
        width * height * depth,
        2
    )


# ---------------------------------------
# Cylinder
# ---------------------------------------

def cylinder_volume(width, height):

    radius = width / 2

    volume = math.pi * radius * radius * height

    return round(volume, 2)


# ---------------------------------------
# Sphere
# ---------------------------------------

def sphere_volume(diameter):

    radius = diameter / 2

    volume = (4 / 3) * math.pi * (radius ** 3)

    return round(volume, 2)


# ---------------------------------------
# Main Function
# ---------------------------------------

def calculate_volume(shape, width, height, depth):

    shape = shape.lower()

    if shape == "cuboid":

        return cuboid_volume(
            width,
            height,
            depth
        )

    elif shape == "rounded cuboid":

        return cuboid_volume(
            width,
            height,
            depth
        )

    elif shape == "cylinder":

        return cylinder_volume(
            width,
            height
        )

    elif shape == "sphere":

        return sphere_volume(width)

    return None