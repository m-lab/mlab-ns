from google.appengine.ext import db

from mlabns.db import model
from mlabns.third_party import ipaddr
from mlabns.util import constants

import logging
import os
import socket
import string
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__),
    "../third_party/pygeoip")))
import pygeoip

# For more details about the decimal representation of the IP addresses
# used in the CVS files and the conversion algorithm see
# http://www.maxmind.com/app/csv.

class GeoRecord:
    def __init__(self, city=None, country=None, latitude=None, longitude=None):
        self.city = city
        self.country = country
        self.latitude = latitude
        self.longitude = longitude


def get_ip_geolocation(remote_addr,
        db_type=constants.GEOLOCATION_MAXMIND_USE_FILE):
    """Returns the geolocation data associated with an IP address.

    Args:
        remote_addr: A string describing an IPv4 or IPv6 address.
        db_type: An indicator whether to use the Mamind datastore or file.

    Returns:
        A GeoRecord if the geolocation data is found in the db,
        otherwise an empty GeoRecord.
    """

    if db_type == constants.GEOLOCATION_MAXMIND_USE_FILE:
        try:
            return get_ip_geolocation_datafile(remote_addr)
        except socket.error:
            pass
    elif db_type == constants.GEOLOCATION_MAXMIND_USE_DATASTORE:
        try:
            return get_ipv4_geolocation_datastore(remote_addr)
        except ipaddr.AddressValueError:
            pass

        try:
            return get_ipv6_geolocation_datastore(remote_addr)
        except ipaddr.AddressValueError:
            pass

    # Return an empty GeoRecord.
    logging.warning('Returning empty record')
    return GeoRecord()

def get_ip_geolocation_datafile(remote_addr,
        city_file=constants.GEOLOCATION_MAXMIND_CITY_FILE):
    """Returns the geolocation data associated with an IPv4 address retrieved
    from the Maxmind database through the pygeoip module.

    Args:
        remote_addr: A string describing an IP address (v4 or v6).
        city_file: The path to the Maxmind .dat file.

    Returns:
        A GeoRecord containing the geolocation data if is found in the db,
        otherwise an empty GeoRecord.

    Raises:
        socket.error, if 'remote_addr' is not a valid IP address.
    """
    geo_record = GeoRecord()

    geo_city_block = pygeoip.GeoIP(city_file,
        flags=pygeoip.const.MEMORY_CACHE).record_by_addr(remote_addr)

    if geo_city_block is None:
        logging.error('IP %s not found in the Maxmind database.',
            str(remote_addr))
        return geo_record

    geo_record.city = geo_city_block['city']
    geo_record.country = geo_city_block['country_code']
    geo_record.latitude = geo_city_block['latitude']
    geo_record.longitude = geo_city_block['longitude']
    return geo_record

def get_ipv4_geolocation_datastore(remote_addr,
        ipv4_table=model.MaxmindCityBlock,
        city_table=model.MaxmindCityLocation):
    """Returns the geolocation data associated with an IPv4 address retrieved
    from the Maxmind database in the GAE Datastore.

    Args:
        remote_addr: A string describing an IPv4 address.

    Returns:
        A GeoRecord containing the geolocation data if is found in the db,
        otherwise an empty GeoRecord.

    Raises:
        ipaddr.AddressValueError, if 'remote_addr' is not a valid IPv4 address.
    """
    geo_record = GeoRecord()
    ip_num = int(ipaddr.IPv4Address(remote_addr))

    geo_city_block = ipv4_table.gql(
        'WHERE start_ip_num <= :ip_num '
        'ORDER BY start_ip_num DESC',
        ip_num=ip_num).get()
    if geo_city_block is None or geo_city_block.end_ip_num < ip_num:
        logging.error('IP %s not found in the Maxmind database.', str(ip_num))
        return geo_record

    location = city_table.get_by_key_name(geo_city_block.location_id)
    if location is None:
        logging.error(
            'Location %s not found in the Maxmind database.', remote_addr)
        return geo_record

    geo_record.city = location.city
    geo_record.country = location.country
    geo_record.latitude = location.latitude
    geo_record.longitude = location.longitude
    return geo_record

def get_ipv6_geolocation_datastore(remote_addr,
                         ipv6_table=model.MaxmindCityBlockv6):
    """Returns the geolocation data associated with an IPv6 address.

    Args:
        remote_addr: A string describing an IPv6 address.

    Returns:
        A GeoRecord containing the geolocation data if found,
        otherwise an empty GeoRecord.

    Raises:
        ipaddr.AddressValueError, if 'remote_addr' is not a valid IPv6 address.
    """
    geo_record = GeoRecord()
    ip_num = int(ipaddr.IPv6Address(remote_addr))
    # We currently keep only /64s in the MaxmindCityBlocksv6 db.
    ip_num = (ip_num >> 64)

    geo_city_block_v6 = ipv6_table.gql(
        'WHERE start_ip_num <= :ip_num '
        'ORDER BY start_ip_num DESC',
        ip_num=ip_num).get()
    if geo_city_block_v6 is None or geo_city_block_v6.end_ip_num < ip_num:
        logging.error('IP %s not found in the Maxmind database.', str(ip_num))
        return geo_record

    geo_record.city = constants.UNKNOWN_CITY
    geo_record.country = geo_city_block_v6.country
    geo_record.latitude = geo_city_block_v6.latitude
    geo_record.longitude = geo_city_block_v6.longitude
    return geo_record

def get_country_geolocation(country, country_table=model.CountryCode):
    """Returns the geolocation data associated with a country code.

    Args:
        country: A string describing a two alphanumeric country code.

    Returns:
        A GeoRecord containing the geolocation data if found,
        otherwise an empty GeoRecord.
    """
    geo_record = GeoRecord()

    logging.info('Retrieving geolocation info for country %s.', country)
    location = country_table.get_by_key_name(country)
    if location is not None:
        geo_record.city = constants.UNKNOWN_CITY
        geo_record.country = location.alpha2_code
        geo_record.latitude = location.latitude
        geo_record.longitude = location.longitude
    return geo_record

def get_city_geolocation(city, country, city_table=model.MaxmindCityLocation):
    """Returns the geolocation data associated with a city and country code.

    Args:
        city: A string specifying the name of the city.
        country: A string describing a two alphanumeric country code.

    Returns:
        A GeoRecord containing the geolocation data if found,
        otherwise an empty GeoRecord.
    """
    geo_record = GeoRecord()

    logging.info('Retrieving geolocation info for country %s, city %s.',
                 city, country)
    location = city_table.gql(
        'WHERE city = :city AND country = :country',
        city=city,country=country).get()
    if location is None:
        logging.error(
            '%s, %s not found in the database.', city, country)
        return geo_record

    geo_record.city = location.city
    geo_record.country = location.country
    geo_record.latitude = location.latitude
    geo_record.longitude = location.longitude
    return geo_record
