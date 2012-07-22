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
FORMAT_HTML     = 'html'
FORMAT_PROTOBUF = 'protobuf'
HEADER_CITY     = 'X-AppEngine-City'
HEADER_COUNTRY  = 'X-AppEngine-Country'
HEADER_LAT_LONG = 'X-AppEngine-CityLatLong'
LAT_LONG        = 'lat_long'
METRO           = 'metro'
POLICY          = 'policy'
POLICY_GEO      = 'geo'
RESPONSE_TYPE   = 'format'
RESPONSE_FORMAT = 'format'
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
TOOL_NAME       = 'tool'
URL             = 'url'
USER_CITY       = 'city'
USER_COUNTRY    = 'country'
USER_IPv4       = 'addr_ipv4'
USER_IPv6       = 'addr_ipv6'

class Error(Exception): pass
class FormatError(Error): pass

class Message():
    def __init__(self):
        self.timestamp = None
        self.signature = None

    def compute_signature(self, key):
        """Computes the signature of this Message.

        Args:
            key: A string representing the cryptographic key used to
                compute the signature.

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
        """Updates the 'timestamp' field with the current time."""

        self.timestamp = str(int(time.time()))

    def sign(self, key):
        """Updates the 'signature' field of this Message.

        Args:
            key: A string representing the key that is used to compute
                the signature.
        """
        self.signature = self.compute_signature(key);

    def verify_signature(self, key):
        """Verifies the signature of this Message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        Returns:
            True if the signature is correct, False otherwise.
        """

        signature = self.compute_signature(key)
        return (signature == self.signature)

    def initialize_from_dictionary(self, dictionary):
        """Initializes the fields of this Message from the input dict.

        Args:
            dictionary: A dict containing the fields and values to
                initialize this Message.

        Raises:
            FormatError: An error occured if the input dictionary does
                not contain one or more required fields.
        """
        pass

    def to_dictionary(self):
        """Creates a dict containing the fields of this Message.

        Returns:
            A dict containing the fields of this Message.
        """
        pass
