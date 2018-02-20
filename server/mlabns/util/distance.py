import math

from mlabns.util import constants


def distance(lat1, lon1, lat2, lon2):
    """Computes the distance between two points.

    This is a python implementation of Haversine formula to find
    the distance between two latitude/longitude points. For more details, see
    http://en.wikipedia.org/wiki/Haversine_formula.

    Args:
        lat1: A float representing the latitude of the origin point.
        lon1: A float representing the longitude of the origin point.
        lat2: A float representing the latitude of the destination point.
        lon2: A float representing the longitude of the destination point.

    Returns:
        A float representing distance in km from origin to destination.
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = constants.EARTH_RADIUS * c

    return d
