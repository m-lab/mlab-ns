import math

def distance(origin, destination):
    """Computes the distance between two points.
    
    Args:
        origin: A string of the form 'lat,long' representing the
            geographical location of the origin point.
        destination: A string of the form 'lat,long' representing
            the geographical location of the destination point. 

    Return:
        A float representing distance in km from origin to destination.
    """ 
    lat1, lon1 = [float(x) for x in origin.split(',')]
    lat2, lon2 = [float(x) for x in destination.split(',')]
    radius = 6371

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d
