from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import base64
import hashlib
import hmac
import logging
import string
import time

CITY            = 'city'
COUNTRY         = 'country'
ENTITY          = 'entity'
ENTITY_SITE     = 'site'
ENTITY_SLIVER_TOOL = 'sliver_tool'
HEADER_CITY     = 'X-AppEngine-City'
HEADER_COUNTRY  = 'X-AppEngine-Country'
HEADER_LAT_LONG = 'X-AppEngine-CityLatLong'
LAT_LONG        = 'lat_long'
METRO           = 'metro'
POLICY          = 'policy'
POLICY_GEO      = 'geo'
SERVER_ID       = 'server_id'
SIGNATURE       = 'sign'
SITE_ID         = 'site_id'
SLICE_ID        = 'slice_id'
SLIVER_IPv4     = 'sliver_ipv4'
SLIVER_IPv6     = 'sliver_ipv6'
SLIVER_TOOL_KEY = 'sliver_tool_key'
STATUS          = 'status'
STATUS_ERROR    = 'error'
STATUS_OFFLINE  = 'offline'
STATUS_ONLINE   = 'online'
STATUS_REGISTERED = 'init'
TIMESTAMP       = 'timestamp'
TOOL_ID         = 'tool_id'
URL             = 'url'

class Error(Exception): pass
class FormatError(Error): pass

class Message():

    def __init__(self):
        self.data = {}

    def compute_signature(self, key):
        """Computes a signature of the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        Return:
            A string representing the signature.
        """
        value_list = []
        for item in sorted(self.data.iterkeys()):
            logging.debug(self.data[item])
            if item != SIGNATURE:
                value_list.append(self.data[item])

        key = key.encode('ascii')
        values_str = string.join(value_list, '')
        digest = hmac.new(key, values_str, hashlib.sha1).digest()
        signature = base64.encodestring(digest).strip()
        logging.debug(signature)

        return signature

    def to_dictionary(self):
        return self.data

    def sign(self, key):
        """Adds a signature to the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        """
        self.data[SIGNATURE] = self.compute_signature(key);

    def is_signed(self):
        return self.data.has_key(SIGNATURE)

    def verify_signature(self, key):
        """Verifies the signature of the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        Return:
            True if the signature is correct, False otherwise.
        """

        signature = self.compute_signature(key)
        return (signature == self.data[SIGNATURE])

    def read_from_dictionary(
        self,
        dictionary,
        required_keys = [],
        optional_keys = []):

        for required_key in required_keys:
            if not dictionary.has_key(required_key):
                raise FormatError('Missing %s.' % (required_key))

        for optional_key in optional_keys:
            if not dictionary.has_key(optional_key):
                logging.info('Missing %s.', optional_key)

        for i in dictionary.iterkeys():
            self.data[i] = dictionary[i]


class UpdateMessage(Message):

    def __init__(self):
        Message.__init__(self)

        self.required_keys = set([])
        self.optional_keys = set([])

        self.add_required_key(SERVER_ID)
        self.add_required_key(SITE_ID)
        self.add_required_key(SLICE_ID)
        self.add_required_key(SLIVER_IPv4)
        self.add_required_key(SLIVER_IPv6)
        self.add_required_key(STATUS)
        self.add_required_key(TOOL_ID)
        self.add_required_key(URL)

        self.add_optional_key(SIGNATURE)
        self.add_optional_key(TIMESTAMP)

        for key in self.required_keys:
            self.data[key] =''

    def read_from_dictionary(self, dictionary):
        Message.read_from_dictionary(
            self,
            dictionary,
            self.required_keys,
            self.optional_keys)

    def add_timestamp(self):
        self.add_optional_key(TIMESTAMP)
        self.data[TIMESTAMP] = str(int(time.time()))

    def add_required_key(self, required_key):
        self.required_keys.add(required_key)

    def add_optional_key(self, optional_key):
        self.optional_keys.add(optional_key)

    def set_tool_id(self, tool_id):
        self.data[TOOL_ID] = tool_id

    def get_tool_id(self):
        return self.data[TOOL_ID]

    def set_slice_id(self, slice_id):
        self.data[SLICE_ID] = slice_id

    def get_slice_id(self):
        return self.data[SLICE_ID]

    def set_server_id(self, server_id):
        self.data[SERVER_ID] = server_id

    def get_server_id(self):
        return self.data[SERVER_ID]

    def set_site_id(self, site_id):
        self.data[SITE_ID] = site_id

    def get_site_id(self):
        return self.data[SITE_ID]

    def set_sliver_ipv4(self, sliver_ipv4):
        self.data[SLIVER_IPv4] = sliver_ipv4

    def get_sliver_ipv4(self):
        return self.data[SLIVER_IPv4]

    def set_sliver_ipv6(self, sliver_ipv6):
        self.data[SLIVER_IPv6] = sliver_ipv6

    def get_sliver_ipv6(self):
        return self.data[SLIVER_IPv6]

    def set_url(self, url):
        self.data[URL] = url

    def get_url(self):
        return self.data[URL]

    def set_timestamp(self, timestamp):
        self.data[TIMESTAMP] = timestamp

    def get_timestamp(self):
        return self.data[TIMESTAMP]

    def set_status(self, status):
        self.data[STATUS] = status

    def get_status(self):
        return self.data[STATUS]

    def set_signature(self, signature):
        self.data[STATUS] = signature

    def get_signature(self):
        return self.data[SIGNATURE]


class RegistrationMessage(Message):

    def __init__(self):
        Message.__init__(self)

        self.site_required_keys = set([])
        self.site_optional_keys = set([])
        self.sliver_tool_required_keys = set([])
        self.sliver_tool_optional_keys = set([])

        self.site_required_keys.add(ENTITY)
        self.site_required_keys.add(CITY)
        self.site_required_keys.add(COUNTRY)
        self.site_required_keys.add(ENTITY)
        self.site_required_keys.add(LAT_LONG)
        self.site_required_keys.add(METRO)

        self.site_optional_keys.add(SIGNATURE)
        self.site_optional_keys.add(TIMESTAMP)

        self.sliver_tool_required_keys.add(ENTITY)
        self.sliver_tool_required_keys.add(SERVER_ID)
        self.sliver_tool_required_keys.add(SITE_ID)
        self.sliver_tool_required_keys.add(SLICE_ID)
        self.sliver_tool_required_keys.add(SLIVER_IPv4)
        self.sliver_tool_required_keys.add(SLIVER_IPv6)
        self.sliver_tool_required_keys.add(SLIVER_TOOL_KEY)
        self.sliver_tool_required_keys.add(STATUS)
        self.sliver_tool_required_keys.add(TOOL_ID)
        self.sliver_tool_required_keys.add(URL)

        self.sliver_tool_optional_keys.add(TIMESTAMP)
        self.sliver_tool_optional_keys.add(SIGNATURE)

        for key in self.sliver_tool_required_keys:
            self.data[key] =''

        for key in self.site_required_keys:
            self.data[key] =''

    def add_site_required_key(self, required_key):
        self.site_required_keys.add(required_key)

    def add_site_optional_key(self, optional_key):
        self.site_optional_keys.add(optional_key)

    def add_sliver_tool_required_key(self, required_key):
        self.sliver_tool_required_keys.add(required_key)

    def add_sliver_tool_optional_key(self, optional_key):
        self.sliver_tool_optional_keys.add(optional_key)

    def read_from_dictionary(self, dictionary):
        if not dictionary.has_key(ENTITY):
            raise FormatError('Missing entity key.')
        elif dictionary[ENTITY] == ENTITY_SITE:
            Message.read_from_dictionary(
                self,
                dictionary,
                self.site_required_keys,
                self.site_optional_keys)
        elif dictionary[ENTITY] == ENTITY_SLIVER_TOOL:
            Message.read_from_dictionary(
                self,
                dictionary,
                self.sliver_tool_required_keys,
                self.sliver_tool_optional_keys)
        else:
            raise FormatError('Missing entity key.')

    def is_site(self):
        return (self.data[ENTITY] == ENTITY_SITE)

    def is_sliver_tool(self):
        return (self.data[ENTITY] == ENTITY_SLIVER_TOOL)

    def add_timestamp(self):
        self.data[TIMESTAMP] = str(int(time.time()))

    def set_tool_id(self, tool_id):
        self.data[TOOL_ID] = tool_id

    def get_tool_id(self):
        return self.data[TOOL_ID]

    def set_slice_id(self, slice_id):
        self.data[SLICE_ID] = slice_id

    def get_slice_id(self):
        return self.data[SLICE_ID]

    def set_server_id(self, server_id):
        self.data[SERVER_ID] = server_id

    def get_server_id(self):
        return self.data[SERVER_ID]

    def set_site_id(self, site_id):
        self.data[SITE_ID] = site_id

    def get_site_id(self):
        return self.data[SITE_ID]

    def set_sliver_ipv4(self, sliver_ipv4):
        self.data[SLIVER_IPv4] = sliver_ipv4

    def get_sliver_ipv4(self):
        return self.data[SLIVER_IPv4]

    def set_sliver_ipv6(self, sliver_ipv6):
        self.data[SLIVER_IPv6] = sliver_ipv6

    def get_sliver_ipv6(self):
        return self.data[SLIVER_IPv6]

    def set_sliver_tool_key(self, key):
        self.data[SLIVER_TOOL_KEY] = key

    def get_sliver_tool_key(self):
        return self.data[SLIVER_TOOL_KEY]

    def set_url(self, url):
        self.data[URL] = url

    def get_url(self):
        return self.data[URL]

    def set_timestamp(self, timestamp):
        self.data[TIMESTAMP] = timestamp

    def get_timestamp(self):
        return self.data[TIMESTAMP]

    def set_status(self, status):
        self.data[STATUS] = status

    def get_status(self):
        return self.data[STATUS]

    def set_signature(self, signature):
        self.data[STATUS] = signature

    def get_signature(self):
        return self.data[SIGNATURE]

    def set_city(self, city):
        self.data[CITY] = city

    def get_city(self):
        return self.data[CITY]

    def set_country(self, country):
        self.data[COUNTRY] = country

    def get_country(self):
        return self.data[COUNTRY]

    def set_lat_long(self, lat_long):
        self.data[lat_long] = lat_long

    def get_lat_long(self):
        return self.data[LAT_LONG]

    def set_metro(self, metro):
        self.data[METRO] = metro

    def get_metro(self):
        return self.data[METRO]


class LookupQuery:
    def __init__(self, request):
        self.tool_id = ''
        self.policy = ''
        self.metro = ''
        self.user_ip = ''
        self.user_city = ''
        self.user_country = ''
        self.user_lat_long = ''

        parts = request.path.strip('/').split('/')
        self.tool_id = parts[0]
        self.user_ip = request.remote_addr
        self.policy = request.get(POLICY)
        self.metro = request.get(METRO)

        # Default to geo policy.
        if not self.policy:
            self.policy = POLICY_GEO

        if HEADER_CITY in request.headers:
            self.user_city = request.headers[HEADER_CITY]
        if HEADER_COUNTRY in request.headers:
            self.user_country = request.headers[HEADER_COUNTRY]
        if HEADER_LAT_LONG in request.headers:
            self.user_lat_long = request.headers[HEADER_LAT_LONG]

        logging.info('Policy is "%s".', self.policy)

    def policy_geo(self):
        return self.policy == POLICY_GEO

    def policy_rtt(self):
        return False

