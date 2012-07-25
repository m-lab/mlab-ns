#! /usr/bin/env python

# The design documentation can be found at http://goo.gl/48S22.

import ConfigParser
import logging
import string
import time
import urllib
import urllib2

from Crypto.Cipher import DES3
from optparse import OptionParser
from os import R_OK
from os import access
from os import path

from mlabns.util import message
from mlabns.util import registration_message

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
            fp = open(config_file)
        except IOError:
            logging.error(
                'Cannot open the configuration file: %s.',
                config_file)
            return False
        try:
            config.readfp(fp)
        except ConfigParser.Error:
            # TODO(claudiu) Trigger an event/notification.
            logging.error(
                'Cannot read the configuration file: %s.',
                config_file)
            return False
        fp.close()

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

            if message.ENTITY not in dictionary:
                logging.error('Missing entity')
                return False

            registration = None
            if dictionary[message.ENTITY] == message.ENTITY_SITE:
                registration = self.get_site_registration(
                    dictionary)

            if dictionary[message.ENTITY] == message.ENTITY_SLIVER_TOOL:
                registration = self.get_sliver_tool_registration(
                    dictionary)

            if registration is None:
                logging.error(
                    'Unknown entity: %s',
                    dictionary[message.ENTITY])
                return False

            registration.add_timestamp()
            registration.encrypt_message(admin_key)
            self.registrations.append(registration)

        return True

    def get_site_registration(self, dictionary):
        registration = registration_message.SiteRegistrationMessage()
        try:
            registration.initialize_from_dictionary(dictionary)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return None
        return registration

    def get_sliver_tool_registration(self, dictionary):
        registration = registration_message.SliverToolRegistrationMessage()
        try:
            registration.initialize_from_dictionary(dictionary)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return None
        return registration

    def send_requests(self):
        """Sends the registration requests to the server."""

        for registration in self.registrations:
            data = {}
            data[message.ENTITY] = registration.entity
            data[message.SIGNATURE] = registration.signature
            data[message.CIPHERTEXT] = registration.ciphertext

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
