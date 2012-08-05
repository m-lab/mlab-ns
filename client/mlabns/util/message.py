import base64
import hashlib
import hmac
import json
import logging
import string
import time

from Crypto.Cipher import AES

# These constants are all possible fields in a
# message.
CIPHERTEXT      = 'ciphertext'
CITY            = 'city'
COUNTRY         = 'country'
ENTITY          = 'entity'
ENTITY_SITE     = 'site'
ENTITY_SLIVER_TOOL = 'sliver_tool'
FORMAT          = 'format'
FORMAT_HTML     = 'html'
FORMAT_JSON     = 'json'
FORMAT_PROTOBUF = 'protobuf'
HEADER_CITY     = 'X-AppEngine-City'
HEADER_COUNTRY  = 'X-AppEngine-Country'
HEADER_LAT_LONG = 'X-AppEngine-CityLatLong'
LAT_LONG        = 'lat_long'
METRO           = 'metro'
POLICY          = 'policy'
POLICY_GEO      = 'geo'
REMOTE_ADDRESS  = 'ip'
RESPONSE_FORMAT = 'format'
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
TOOL_NAME       = 'tool'
URL             = 'url'
USER_CITY       = 'city'
USER_COUNTRY    = 'country'
USER_IPv4       = 'addr_ipv4'
USER_IPv6       = 'addr_ipv6'

class Error(Exception): pass
class FormatError(Error): pass
class DecryptionError(Error): pass

class Message():
    def __init__(self):
        self.timestamp = None
        self.signature = None
        self.ciphertext = None
        self.padding = '#'
        self.block_size = 32
        self.inizialization_vector = 'x' * 16

    def add_timestamp(self):
        """Updates the 'timestamp' field with the current time."""
        self.timestamp = str(int(time.time()))

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

    def compute_signature(self, secret_key):
        """Computes the signature of this Message.

        Args:
            key: A string representing the cryptographic key used to
                compute the signature.

        Returns
            A string representing the signature.
        """
        dictionary = self.to_dictionary()

        value_list = []
        for item in sorted(dictionary.iterkeys()):
            logging.debug(
                'data[%s] = %s', item, dictionary[item])
            value_list.append(dictionary[item])

        # Encode the key as ASCII and ignore non ASCII characters.
        key = bytes(secret_key)
        values_str = ''.join(value_list)
        digest = hmac.new(key, values_str, hashlib.sha1).digest()
        signature = base64.encodestring(digest).strip()

        return signature

    def encrypt_message(self, secret_key):
        """Encrypts and signs this Message.

        Args:
            key: A string representing the key that is used to compute
                the signature.
        """
        key = bytes(secret_key)
        plaintext = json.dumps(self.to_dictionary())
        self.ciphertext = self._encrypt_AES(
            plaintext, key, self.block_size, self.padding)

        digest = hmac.new(
            key, self.ciphertext, hashlib.sha1).digest()
        self.signature = base64.encodestring(digest).strip()

    def decrypt_message(self, data, secret_key):
        """Verifies and initializes the fields from an encrypted message.

        Args:
            data: A dict containing the encrypted ciphertext and the
                signature.
            key: A string representing the cryptographic key that
                is used to verify and decrypt the data.
        """
        if SIGNATURE not in data:
            raise DecryptionError('Missing signature.')
        if CIPHERTEXT not in data:
            raise DecryptionError('Missing encrypted payload.')

        # Remove default unicode encoding.
        key = bytes(secret_key)

        digest = hmac.new(
            key, data[CIPHERTEXT], hashlib.sha1).digest()
        signature = base64.encodestring(digest).strip()

        logging.info('key: %s', secret_key)
        logging.info('Cipertext: %s', data[CIPHERTEXT])
        logging.info('Computed signature: %s', signature)
        logging.info('Signature: %s', data[SIGNATURE])

        if (signature != data[SIGNATURE]):
            raise DecryptionError('Bad signature.')

        plaintext = self._decrypt_AES(
            data[CIPHERTEXT], secret_key, self.padding)

        logging.info('Plaintext: %s', plaintext)

        dictionary = json.loads(plaintext)
        self.initialize_from_dictionary(dictionary)

    def _add_padding(self, plaintext, block_size, padding):
        """Adds a padding to the plaintext.

        Args:
            plaintext: A string representing the plaintext to be padded.
            block_size: An integer representing the size of the block.
                After the padding, the length of resulting plaintext will
                be a multiple of this size.
            padding: A character used to pad the plaintext.

        Returns:
            A string representing the padded plaintext.
        """
        return plaintext + \
            (block_size - len(plaintext) % block_size) * padding

    def _encrypt_AES(self, text, secret_key, block_size, padding):
        """Encrypts a string using AES.

        Args:
            text: A string representing the plaintext.
            secret_key: A string representing the cryptographic key used
                for the encryption.
            block_size: An integer that specifies the size of the block
                in the AES encryption scheme.
            padding: A character to be added as padding in order to make
                the length of the plaintext a multiple of block_size.

        Returns:
            A string representing the encrypted text.
        """
        key = bytes(secret_key)
        cipher = AES.new(key, AES.MODE_CBC, self.inizialization_vector)
        plaintext = self._add_padding(text, block_size, padding)
        return base64.b64encode(cipher.encrypt(plaintext))

    def _decrypt_AES(self, ciphertext, secret_key, padding):
        """Decrypts a ciphertext encrypted with  AES.

        Args:
            ciphertext: A string representing the ciphertext.
            secret_key: A string representing the cryptographic key used
                for the encryption.
            padding: A character that was added as padding to the
                plaintext in the encryption procedure.

        Returns:
            A string representing the decrypted ciphertext.
        """
        key = bytes(secret_key)
        cipher = AES.new(key, AES.MODE_CBC, self.inizialization_vector)
        return cipher.decrypt(base64.b64decode(ciphertext)).rstrip(padding)

    def to_dictionary(self):
        """Creates a dict containing the fields of this Message.

        Returns:
            A dict containing the fields of this Message.
        """
        pass
