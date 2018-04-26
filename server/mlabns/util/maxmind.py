from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message

import logging
import os
import socket
import sys

sys.path.insert(1, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../third_party/GeoIP2-python')))
import geoip2.database
import geoip2.errors


class GeoRecord:

    def __init__(self, city=None, country=None, latitude=None, longitude=None):
        self.city = city
        self.country = country
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, other):
        return ((self.city == other.city) and
                (self.country == other.country) and
                (self.latitude == other.latitude) and
                (self.longitude == other.longitude))

    def __ne__(self, other):
        return not self.__eq__(other)


def get_ip_geolocation(ip_address):
    """Returns the geolocation data associated with an IP address from MaxMind.

    Args:
        ip_address: A string describing an IP address (v4 or v6).

    Returns:
        A populated GeoRecord if matching geolocation data is found for the
        IP address. Otherwise, an empty GeoRecord.
    """
    try:
        geo_reader = geoip2.database.Reader(os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../../%s' %
            constants.GEOLOCATION_MAXMIND_CITY_FILE)))
        geo_response = geo_reader.city(ip_address)
    except ValueError, e:
        logging.error('Malformed IP address %s for MaxMind lookup: %s',
                      ip_address, e)
        return GeoRecord()
    except geoip2.errors.AddressNotFoundError, e:
        logging.error('IP address not found in MaxMind database: %s',
                      ip_address)
        return GeoRecord()

    if not geo_response:
        logging.error('IP %s not found in the MaxMind database.', ip_address)
        return GeoRecord()

    return GeoRecord(city=geo_response.city.name,
                     country=geo_response.country.iso_code,
                     latitude=geo_response.location.latitude,
                     longitude=geo_response.location.longitude)


def get_country_geolocation(country, country_table=model.CountryCode):
    """Returns the geolocation data associated with a country code.

    Args:
        country: A string describing a two alphanumeric country code.
        country_table: Datastore table from which to retrieve country
            information.

    Returns:
        A GeoRecord containing the geolocation data if found, otherwise an
        empty GeoRecord.
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
        city_table: Datastore table from which to retrieve city information.

    Returns:
        A GeoRecord containing the geolocation data if found, otherwise an empty
        GeoRecord.
    """
    geo_record = GeoRecord()

    logging.info('Retrieving geolocation info for country %s, city %s.', city,
                 country)
    location = city_table.gql('WHERE city = :city AND country = :country',
                              city=city,
                              country=country).get()
    if location is None:
        logging.error('%s, %s not found in the database.', city, country)
        return geo_record

    geo_record.city = location.city
    geo_record.country = location.country
    geo_record.latitude = location.latitude
    geo_record.longitude = location.longitude
    return geo_record
