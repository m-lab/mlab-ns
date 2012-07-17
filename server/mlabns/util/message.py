import base64
import hashlib
import hmac
import string
import time

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
        self.timestamp = None
        self.signature = None

    def compute_signature(self, key):
        """Computes the signature of the message.

        Args:
            key: A string representing the key.

        Returns
            A string representing the signature.
        """

        dictionary = self.to_dictionary()
        dictionary[SIGNATURE] = ''

        value_list = []
        for item in sorted(dictionary.iterkeys()):
            value_list.append(dictionary[item])

        # Encode the key as ASCII and ignore non ASCII characters.
        key = key.encode('ascii', 'ignore')
        values_str = string.join(value_list, '')
        digest = hmac.new(key, values_str, hashlib.sha1).digest()
        signature = base64.encodestring(digest).strip()

        return signature

    def add_timestamp(self):
        """Adds a timestamp to the message."""

        self.timestamp = str(int(time.time()))

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

        Returns:
            True if the signature is correct, False otherwise.
        """

        signature = self.compute_signature(key)
        return (signature == self.signature)

    def initialize_from_dictionary(self, dictionary):
        """Reads the Message from a dict.

        Args:
            dictionary: The dict containing the data.

        Raises:
            FormatError: An error occured if some required field is
                missing.
        """
        pass

    def to_dictionary(self):
        """Convert the Message into a dict.

        Returns:
            A dict containing the data.
        """
        pass
