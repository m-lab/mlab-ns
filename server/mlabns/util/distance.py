import math

def distance(lat1, lon1, lat2, lon2):
    """Computes the distance between two points.

    Args:
        lat1: A float representing the latitude of the origin point.
        lon1: A float representing the longitude of the origin point.
        lat2: A float representing the latitude of the destination point.
        lon2: A float representing the longitude of the destination point.

    Returns:
        A float representing distance in km from origin to destination.
    """
    radius = 6371

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d
