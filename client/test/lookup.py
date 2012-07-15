#! /usr/bin/env python

import ConfigParser
import urllib
import urllib2
from optparse import OptionParser
from os import path
from os import access
from os import R_OK

import logging

URL = 'url'
HEADER_CITY     = 'x-appengine-city'
HEADER_COUNTRY  = 'x-appengine-country'
HEADER_LAT_LONG = 'x-appengine-citylatlong'

class Error(Exception): pass
class FormatError(Error): pass

class LookupRequest():

    def __init__(self):
        self.url = ''
        self.headers = {}
        self.required_headers = set([
        HEADER_CITY,
        HEADER_COUNTRY,
        HEADER_LAT_LONG])

    def read_from_dictionary(self, dictionary):
        for key in dictionary:
            logging.info('data[%s] = %s', key, dictionary[key])

        if URL not in dictionary:
            raise FormatError('Missing URL')

        self.url = dictionary[URL]

        for header in self.required_headers:
            if header not in dictionary:
                raise FormatError('Missing %s.' % (header))
            else:
                self.headers[header] = dictionary[header]

class LookupClient:
    """Perform lookup requests."""

    def __init__(self):
        self.requests = []

    def read_configuration(self, config_file):
        """Reads lookup requests from a file.

        The parameters are specified in the ConfigParser format(e.g):

        [london-01]
        url: http://localhost:8080/npad?metro=ath
        X-AppEngine-City: london
        X-AppEngine-Region: eng
        X-AppEngine-Country: GB
        X-AppEngine-CityLatLong: 51.513330,-0.088947

        Args:
          config_file: A file containing the data configuration.
        """

        config = ConfigParser.ConfigParser()
        try:
            config.read(config_file)
        except ConfigParser.Error, e:
            logging.error('Cannot read the configuration file: %s.', e)
            exit(-1)

        for section in config.sections():
            dictionary = {}
            for option in config.options(section):
                dictionary[option] = config.get(section, option)

            request = LookupRequest()
            try:
                request.read_from_dictionary(dictionary)
            except FormatError, e:
                logging.error('Format error: %s', e)
                return False
            self.requests.append(request)

        return True

    def send_requests(self):
        """Sends the requests to the server."""

        for request in self.requests:
            req = urllib2.Request(request.url, None, request.headers)
            logging.info('Request:')
            logging.info('URL = %s', request.url)
            for header in request.headers:
                logging.info(
                    'header[%s] = "%s"',
                    header,
                    request.headers[header])

            logging.info('Sending...\n')
            try:
                response = urllib2.urlopen(req)
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

    (options, args) = parser.parse_args()
    if options.filename is None:
        logging.error('Missing configuration file.')
        parser.print_help()
        exit(-1)

    config_file = options.filename
    if  not path.exists(config_file):
        logging.error('%s does not exist.', config_file)
        exit(-1)

    if not path.isfile(config_file):
        logging.error('%s is not a file.', config_file)
        exit(-1)

    if not access(config_file, R_OK):
        logging.error('Cannot read %s.', config_file)
        exit(-1)

    client = LookupClient()
    client.read_configuration(config_file)
    client.send_requests()

if __name__ == '__main__':
    main()
