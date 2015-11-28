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
        city_file=constants.GEOLOCATION_MAXMIND_CITY_FILE):
    """Returns the geolocation data associated with an IPv4 address retrieved
    from the Maxmind database through the pygeoip module.

    Args:
        remote_addr: A string describing an IP address (v4 or v6).
        city_file: The path to the Maxmind .dat file.

    Returns:
        A GeoRecord containing the geolocation data if is found in the db,
        otherwise an empty GeoRecord.
    """
    geo_record = GeoRecord()

    try:
        geo_city_block = pygeoip.GeoIP(city_file,
                flags=pygeoip.const.STANDARD).record_by_addr(remote_addr)
    except (socket.error, TypeError):
        logging.warning('Returning empty record')
        return geo_record

    if geo_city_block:
        geo_record.city = geo_city_block['city']
        geo_record.country = geo_city_block['country_code']
        geo_record.latitude = geo_city_block['latitude']
        geo_record.longitude = geo_city_block['longitude']
    else:
        logging.error('IP %s not found in the Maxmind database.',
                str(remote_addr))
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
