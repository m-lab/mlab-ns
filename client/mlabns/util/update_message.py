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
LAT_LONG        = 'lat_long'
MESSAGE_SECTION = 'UpdateMessage'
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

class UpdateMessage():

    def __init__(self):
        self.tool_id = ''
        self.slice_id = ''
        self.server_id = ''
        self.sliver_ipv4 = ''
        self.sliver_ipv6 = ''
        self.status = ''
        self.url = ''
        self.signature = ''
        self.timestamp = ''

        self.required_fields = set([
            SERVER_ID,
            SITE_ID,
            SLICE_ID,
            SLIVER_IPv4,
            SLIVER_IPv6,
            STATUS,
            TOOL_ID,
            URL])

    def initialize_from_dictionary(self, dictionary):
        for field in self.required_fields:
            if field not in dictionary:
                raise FormatError('Missing field %s.' % (field))

        self.tool_id = dictionary[TOOL_ID]
        self.slice_id = dictionary[SLICE_ID]
        self.server_id = dictionary[SERVER_ID]
        self.site_id = dictionary[SITE_ID]
        self.sliver_ipv4 = dictionary[SLIVER_IPv4]
        self.sliver_ipv6 = dictionary[SLIVER_IPv6]
        self.status = dictionary[STATUS]
        self.url = dictionary[URL]

        if TIMESTAMP in dictionary:
            self.timestamp = dictionary[TIMESTAMP]

        if SIGNATURE in dictionary:
            self.signature = dictionary[SIGNATURE]

    def add_timestamp(self):
        self.timestamp = str(int(time.time()))

    def compute_signature(self, key):
        """Computes a signature of the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        Return:
            A string representing the signature.
        """
        value_list = [
            self.server_id,
            self.site_id,
            self.slice_id,
            self.sliver_ipv4,
            self.sliver_ipv6,
            self.status,
            self.timestamp,
            self.tool_id,
            self.url ]

        key = key.encode('ascii')
        values_str = string.join(value_list, '')
        digest = hmac.new(key, values_str, hashlib.sha1).digest()
        signature = base64.encodestring(digest).strip()
        logging.debug(signature)

        return signature

    def sign(self, key):
        """Adds a signature to the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        """
        self.signature = self.compute_signature(key);

    def verify_signature(self, key):
        """Verifies the signature of the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        Return:
            True if the signature is correct, False otherwise.
        """

        signature = self.compute_signature(key)
        return (signature == self.signature)

    def to_dictionary(self):

        dictionary = {}
        dictionary[SERVER_ID] = self.server_id
        dictionary[SIGNATURE] = self.signature
        dictionary[SITE_ID] = self.site_id
        dictionary[SLICE_ID] = self.slice_id
        dictionary[SLIVER_IPv4] = self.sliver_ipv4
        dictionary[SLIVER_IPv6] = self.sliver_ipv6
        dictionary[STATUS] = self.status
        dictionary[TIMESTAMP] = self.timestamp
        dictionary[TOOL_ID] = self.tool_id
        dictionary[URL] = self.url

        return dictionary
