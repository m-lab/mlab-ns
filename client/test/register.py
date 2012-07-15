#! /usr/bin/env python

# The design documentation can be found at http://goo.gl/48S22.

from optparse import OptionParser
from os import R_OK
from os import access
from os import path
import ConfigParser
import base64
import hashlib
import hmac
import logging
import logging
import string
import time
import time
import urllib
import urllib2

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
        return (dictionary[ENTITY] == ENTITY_SITE)

    def is_sliver_tool(self):
        return (dictionary[ENTITY] == ENTITY_SLIVER_TOOL)

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

    def set_region(self, region):
        self.data[REGION] = region

    def get_region(self):
        return self.data[REGION]

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

class RegistrationClient:
    """Registers SliverTools with the GAE server."""

    def __init__(self):
        # TODO (claudiu) Add comments for each instance var.
        self.server_url = None
        self.registrations = []

    def read_configuration(
        self,
        config_file,
        section_key,
        option_key,
        section_url,
        option_url):

        """Sends SliverTools and sites registrations.

        The config parameters are specified in the ConfigParser format.
        See example of configuration in mlabns/test/register.conf.

        Return:
            True if no error is encountered, False otherwise.
        """
        config = ConfigParser.ConfigParser()
        try:
            config.read(config_file)
            # TODO(claudiu): If the configuration file is not passed
            # as argument use a default location e.g.'/etc/mlab-ns.conf'.
        except ConfigParser.Error, e:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Cannot read the configuration file: %s.', e)
            return False

        admin_key = None
        for section in config.sections():
            if section == section_key:
                admin_key = config.get(section, option_key)
                continue
            if section == section_url:
                self.server_url = config.get(section, option_url)
                continue
            if admin_key is None:
                logging.error('Missing key (section: %s)', section)
                return False
            if self.server_url is None:
                logging.error(
                    'Missing server url (section: %s).',
                     section)
                return False

            logging.info('BEGIN %s', section)
            dictionary = {}
            for option in config.options(section):
                dictionary[option] = config.get(section, option)
                logging.info('%s = "%s"', option, dictionary[option])
            logging.info('END %s\n.', section)

            registration = RegistrationMessage()
            registration.read_from_dictionary(dictionary)
            registration.add_timestamp()
            registration.sign(admin_key)
            self.registrations.append(registration)

        return True

    def send_requests(self):
        """Sends the registration requests to the server."""

        for registration in self.registrations:
            data = registration.to_dictionary()
            encoded_data = urllib.urlencode(data)
            request = urllib2.Request(self.server_url, encoded_data)
            logging.info('Sending request:')
            for key in data.keys():
                logging.info('data[%s] = "%s"', key, data[key])
            try:
                response = urllib2.urlopen(request)
                logging.info('Response: %s\n', response.read())
            except urllib2.URLError, e:
                # TODO(claudiu) Trigger an event/notification.
                logging.error('Cannot send request: %s.\n', e)

def main():
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.DEBUG)

    parser = OptionParser()
    parser.add_option(
        '-f',
        '--file',
        dest='filename',
        help='configuration file')
    parser.add_option(
        '',
        '--section-key',
        dest='section_key',
        default='key',
        help='Name of the key section in the config file')
    parser.add_option(
        '',
        '--options-key',
        dest='option_key',
        default='key',
        help='Name of the option in the "key" section.')
    parser.add_option(
        '',
        '--section-url',
        dest='section_url',
        default='server_url',
        help='Name of the url section in the config file.')
    parser.add_option(
        '',
        '--option-url',
        dest='option_url',
        default='server_url',
        help='Name of the option in the "url" section.')

    (options, args) = parser.parse_args()
    if options.filename is None:
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Missing configuration file.')
        parser.print_help()
        exit(-1)

    config_file = options.filename
    if not path.exists(config_file):
        # TODO(claudiu) Trigger an event/notification.
        logging.error('File %s does not exist.', config_file)
        exit(-1)

    if not path.isfile(config_file):
        # TODO(claudiu) Trigger an event/notification.
        logging.error('%s is not a file.', config_file)
        exit(-1)

    if not access(config_file, R_OK):
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Cannot read file %s.', config_file)
        exit(-1)

    client = RegistrationClient()
    if not client.read_configuration(
        config_file,
        options.section_key,
        options.option_key,
        options.section_url,
        options.option_url):
        logging.error('Cannot read file %s.', config_file)
        exit(-1)

    client.send_requests()

if __name__ == '__main__':
    main()
