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
import string
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


class UpdateClient:
    """Sends SliverTool status updates to the GAE server."""

    def __init__(self):

        # String that represents the URL on the server where the updates
        # are sent.
        self.server_url = None

        # List of the updates to be sent to the server.
        self.updates = []

    def read_configuration(
        self,
        config_file,
        section_key,
        option_key,
        section_url,
        option_url):

        """Reads SliverTool configuration from file.

        The config parameters are specified in the ConfigParser format
        (see http://docs.python.org/library/configparser.html).
        'config_file' usually contains the configuration of a single
        SliverTool. However, it's possible to have the configurations of
        more that one SliverTool in the same file. See example of
        configuration file in the mlabns/test/update.conf.

        Args:
            config_file: A string that represents the name of a file.
            section_key: A string describing the name of the 'key'
                section in the configuration file.
            option_key: A string describing the name of the option
                in the 'key' section.
            section_url: A string describing the name of the 'url'
                section in the configuration file.
            option_url: A string describing the name of the option in
                the 'url' section.

        Return:
            True if no error is encountered, False otherwise.
        """
        config = ConfigParser.ConfigParser()
        try:
            config.read(config_file)
        except ConfigParser.Error, e:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Cannot read the configuration file: %s.', e)
            return False

        sliver_tool_key = None
        for section in config.sections():
            if section == section_key:
                sliver_tool_key = config.get(section, option_key)
                continue
            if section == section_url:
                self.server_url = config.get(section, option_url)
                continue
            if sliver_tool_key is None:
                logging.error('Missing key (section: %s)', section)
                return False
            if self.server_url is None:
                logging.error(
                    'Missing server url (section: %s).',
                    section)
                return False

            logging.info('BEGIN %s', section)
            update = {}
            for option in config.options(section):
                update[option] = config.get(section, option)
                logging.info('%s = "%s"', option, update[option])
            logging.info('END %s\n.', section)

            update_message = UpdateMessage()
            try:
                update_message.initialize_from_dictionary(update)
            except message.FormatError, e:
                logging.error('Format error: %s', e)
                return False

            update_message.add_timestamp()
            update_message.sign(sliver_tool_key)
            self.updates.append(update_message)

        return True

    def send_updates(self):
        """Sends the updates to the server."""

        for update_message in self.updates:
            data = update_message.to_dictionary()
            encoded_data = urllib.urlencode(data)
            request = urllib2.Request(self.server_url, encoded_data)
            logging.info('sending request:')
            for key in data.keys():
                logging.info('data[%s] = "%s"', key, data[key])
            try:
                response = urllib2.urlopen(request)
                logging.info('response: %s\n', response.read())
            except urllib2.URLError, e:
                # todo(claudiu) trigger an event/notification.
                logging.error('cannot send request: %s.\n', e)

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
        # TODO(claudiu): If the configuration file is not passed
        # as an argument use a default location
        # e.g.'/etc/mlab-ns.conf'.
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

    client = UpdateClient()
    if not client.read_configuration(
        config_file,
        options.section_key,
        options.option_key,
        options.section_url,
        options.option_url):

        logging.error('Cannot read file %s.', config_file)
        exit(-1)

    client.send_updates()

if __name__ == '__main__':
    main()
