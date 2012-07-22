from google.appengine.ext import db

# For more details about the decimal representation of the IP addresses
# used in the CVS files and the conversion algorithm see
# http://www.maxmind.com/app/csv.

class GeoRecord:
    def __init__(self):
        self.city = None
        self.country = None
        self.latitude = 0.0
        self.longitude = 0.0

def ipv6_to_long(ipv6_address):
    """Converts an IPv6 address to a long.

    Args:
        ipv6_address: A string representing an IPv6 address.

    Returns:
        A long obtained by converting the IPv6 address in input to a
        decimal representation, according to Maxmind's specifications.

    """
    try:
        int_values = [ int(x,16) for x in ipv6_address.split(':') ]
    except ValueError:
        logging('Bad IPv6 address: %s', ipv6_address)
        return None
    exp = 7
    result = 0
    for value in int_values:
        result = result + value * (2 ** (exp * 16))
        exp = exp - 1

    return result

def ipv4_to_long(ipv4_address):
    """Converts an IPv4 address to a long.

    Args:
        ipv6_address: A string representing an IPv4 address.

    Returns:
        A long obtained by converting the IPv4 address in input to a
        decimal representation, according to Maxmind's specifications.

    """
    try:
        int_values = [ int(x) for x in ipv4_address.split('.') ]
    except ValueError:
        logging('Bad IPv4 address: %s', ipv4_address)
        return None
    exp = 24
    result = 0
    for value in int_values:
        result = result + value * (2 ** exp)
        exp = exp - 8

    return result

