from google.appengine.ext import db

from mlabns.db import model
from mlabns.util import constants

import logging
import socket

# For more details about the decimal representation of the IP addresses
# used in the CVS files and the conversion algorithm see
# http://www.maxmind.com/app/csv.

class GeoRecord:
    def __init__(self):
        self.city = None
        self.country = None
        self.latitude = None
        self.longitude = None

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
        logging.error('Bad IPv6 address: %s', ipv6_address)
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
        logging.error('Bad IPv4 address: %s', ipv4_address)
        return None
    exp = 24
    result = 0
    for value in int_values:
        result = result + value * (2 ** exp)
        exp = exp - 8

    return result

def get_ip_geolocation(remote_addr):
    """Returns the geolocation data associated with an IP address.

    Args:
        remote_addr: A string describing an IPv4 or IPv6 address.

    Returns:
        A GeoRecord if the geolocation data is found in the db,
        otherwise an empty GeoRecord.
    """
    try:
        socket.inet_pton(socket.AF_INET, remote_addr)
        return get_ipv4_geolocation(remote_addr)
    except socket.error:
        pass

    try:
        socket.inet_pton(socket.AF_INET6, remote_addr)
        return get_ipv6_geolocation(remote_addr)
    except socket.error:
        pass

    # Return an empty GeoRecord.
    logging.warning('Returning empty record')
    return GeoRecord()

def get_ipv4_geolocation(remote_addr):
    """Returns the geolocation data associated with an IPv4 address.

    Args:
        remote_addr: A string describing an IPv4 address.

    Returns:
        A GeoRecord containing the geolocation data if is found in the db,
        otherwise an empty GeoRecord.
    """
    geo_record = GeoRecord()
    ip_long = ipv4_to_long(remote_addr)
    if not ip_long:
        return geo_record

    logging.info('IP long is %s.', ip_long)
    geo_city_block = model.MaxmindCityBlock.gql(
        'WHERE start_ip_num <= :ip_num '
        'ORDER BY start_ip_num DESC',
        ip_num=ip_long).get()

    if not geo_city_block or geo_city_block.end_ip_num < ip_num:
        logging.error("IP not found in the Maxmind database.")
        return geo_record

    logging.info("Retrieving geolocation info for %s.", remote_addr)
    location = model.MaxmindCityLocation.get_by_key_name(
        geo_city_block.location_id)
    if not location:
        logging.error(
            "Location %s not found in the Maxmind database.", remote_addr)
        return geo_record

    geo_record.city = location.city
    geo_record.country = location.country
    geo_record.latitude = location.latitude
    geo_record.longitude = location.longitude

    logging.info(
        'City : %s, Country: %s, Latitude :%s, Longitude: %s',
        location.city, location.country,
        location.latitude, location.longitude)
    return geo_record

def get_ipv6_geolocation(remote_addr):
    """Returns the geolocation data associated with an IPv6 address.

    Args:
        remote_addr: A string describing an IPv6 address.

    Returns:
        A GeoRecord containing the geolocation data if found,
        otherwise an empty GeoRecord.
    """
    geo_record = GeoRecord()
    ip_num = ipv6_to_long(remote_addr)
    if not ip_num:
        return geo_record

    # We currently keep only /64s in the MaxmindCityBlocksv6 db.
    ip_num = (ip_num >> 64)

    logging.info('IPv6 num is %s.', ip_num)
    geo_city_block_v6 = model.MaxmindCityBlockv6.gql(
        'WHERE start_ip_num <= :ip_num '
        'ORDER BY start_ip_num DESC',
        ip_num=ip_num).get()

    if not geo_city_block_v6 or geo_city_block_v6.end_ip_num < ip_num:
        logging.error("IP not found in the Maxmind database.")
        return geo_record

    logging.info("Retrieving geolocation info for %s.", remote_addr)
    geo_record.country = geo_city_block_v6.country
    geo_record.latitude = geo_city_block_v6.latitude
    geo_record.longitude = geo_city_block_v6.longitude

    logging.info(
        'Country: %s, Latitude :%s, Longitude: %s',
        geo_record.country, geo_record.latitude, geo_record.longitude)
    return geo_record

def get_country_geolocation(country):
    """Returns the geolocation data associated with a country code.

    Args:
        country: A string describing a two alphanumeric country code.

    Returns:
        A GeoRecord containing the geolocation data if found,
        otherwise an empty GeoRecord.
    """
    geo_record = GeoRecord()

    logging.info("Retrieving geolocation info for %s.", country)
    location = model.CountryCode.get_by_key_name(country)
    if location:
        geo_record.city = constants.UNKNOWN_CITY
        geo_record.country = location.alpha2_code
        geo_record.latitude = location.latitude
        geo_record.longitude = location.longitude
    return geo_record

def get_city_geolocation(city, country):
    """Returns the geolocation data associated with a city and country code.

    Args:
        city: A string specifying the name of the city.
        country: A string describing a two alphanumeric country code.

    Returns:
        A GeoRecord containing the geolocation data if found,
        otherwise an empty GeoRecord.
    """
    geo_record = GeoRecord()

    logging.info("Retrieving geolocation info for %s, %s.", city,country)
    location = model.MaxmindCityLocation.gql(
        'WHERE city = :city AND country = :country',
        city=city,country=country).get()
    if not location:
        logging.error(
            '%s,%s not found in the database.', city, country)
        return get_country_geolocation(country)

    geo_record.city = location.city
    geo_record.country = location.country
    geo_record.latitude = location.latitude
    geo_record.longitude = location.longitude

    return geo_record

