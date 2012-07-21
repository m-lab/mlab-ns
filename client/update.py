#! /usr/bin/env python

# The design documentation can be found at http://goo.gl/48S22.

import ConfigParser
import logging
import string
import time
import urllib
import urllib2

from optparse import OptionParser
from os import R_OK
from os import access
from os import path

from mlabns.util import update_message

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
        configuration file in mlabns/test/update.conf.

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
            fp = open(config_file)
        except IOError:
            logging.error(
                'Cannot open the configuration file: %s.', config_file)
            return False
        try:
            config.readfp(fp)
        except ConfigParser.Error:
            # TODO(claudiu) Trigger an event/notification.
            logging.error(
                'Cannot read the configuration file: %s.', config_file)
            return False
        finally:
            fp.close()

        if (not config.has_section(section_key) or
            not config.has_option(section_key, option_key)):

            logging.error('Missing key section')
            return False
        sliver_tool_key = config.get(section_key, option_key)

        if (not config.has_section(section_url) or
            not config.has_option(section_url, option_url)):

            logging.error('Missing server url section')
            return False
        self.server_url = config.get(section_url, option_url)

        for section in config.sections():
            if section == section_key or section == section_url:
                continue

            logging.info('BEGIN %s', section)
            update = {}
            for option in config.options(section):
                update[option] = config.get(section, option)
                logging.info('%s = "%s"', option, update[option])
            logging.info('END %s\n.', section)

            message = update_message.UpdateMessage()
            try:
                message.initialize_from_dictionary(update)
            except update_message.FormatError, e:
                logging.error('Format error: %s', e)
                return False

            message.add_timestamp()
            message.sign(sliver_tool_key)
            self.updates.append(message)

        return True

    def send_updates(self):
        """Sends the updates to the server."""

        for message in self.updates:
            data = message.to_dictionary()
            encoded_data = urllib.urlencode(data)
            request = urllib2.Request(self.server_url, encoded_data)
            logging.info('sending request:')
            for key in data.keys():
                logging.info('data[%s] = "%s"', key, data[key])
            try:
                response = urllib2.urlopen(request)
                logging.info('response: %s\n', response.read())
            except urllib2.URLError, e:
                # TODO(claudiu) Trigger an event/notification.
                logging.error('cannot send request: %s.\n', e)

def main():
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.DEBUG)

    # TODO(claudiu) Use argpars instead, because OptionParser is deprecated.
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
