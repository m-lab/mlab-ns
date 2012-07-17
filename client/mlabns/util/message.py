import base64
import hashlib
import hmac
import string
import time
import logging

CITY            = 'city'
COUNTRY         = 'country'
ENTITY          = 'entity'
ENTITY_SITE     = 'site'
ENTITY_SLIVER_TOOL = 'sliver_tool'
FORMAT          = 'format'
FORMAT_JSON     = 'json'
FORMAT_PROTOBUF = 'protobuf'
HEADER_CITY     = 'X-AppEngine-City'
HEADER_COUNTRY  = 'X-AppEngine-Country'
HEADER_LAT_LONG = 'X-AppEngine-CityLatLong'
LAT_LONG        = 'lat_long'
METRO           = 'metro'
POLICY          = 'policy'
POLICY_GEO      = 'geo'
RESPONSE_TYPE   = 'format'
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
        self.timestamp = ''
        self.signature = ''

    def compute_signature(self, key, dictionary):
        value_list = []
        for item in sorted(dictionary.iterkeys()):
            value_list.append(dictionary[item])

        key = key.encode('ascii')
        values_str = string.join(value_list, '')
        digest = hmac.new(key, values_str, hashlib.sha1).digest()
        signature = base64.encodestring(digest).strip()
        logging.debug(signature)

        return signature

    def add_timestamp(self):
        self.timestamp = str(int(time.time()))

    def to_dictionary(self):
        pass

    def verify_signature(self, key):
        pass
