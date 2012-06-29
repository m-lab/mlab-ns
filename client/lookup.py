#! /usr/bin/env python

import ConfigParser
import urllib
import urllib2
from optparse import OptionParser
from os import path
from os import access
from os import R_OK

import logging

class LookupClient:
    """Testing only, perform lookup requests."""
    
    def __init__(self):
        self.server_url = None
        self.requests = []
    
    def read_configuration(self, config_file):
        """Reads lookup requests from a file.
         
        The parameters are specified in the ConfigParser format(e.g):
        
        [london-01]
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
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Cannot read the configuration file: %s.', e)
            exit(-1)
        
        for section in config.sections():
            if section == 'server_url':
                self.server_url = config.get(section, 'server_url')
            else:
                logging.info('START %s', section)
                request = {}
                for option in config.options(section):
                    request[option] = config.get(section, option)
                    logging.info(
                        '%s = "%s"',
                        option,
                        config.get(section, option))    
                logging.info('END %s\n.', section)
                self.requests.append(request)

            if self.server_url is None:
                logging.error('Missing server_url.')
                exit(-1)

    def send_requests(self):
        """Sends the requests to the server."""

        url = self.server_url
        for request in self.requests:
            req = urllib2.Request(url, None, request)
            logging.info('Request:')
            for key in request.keys():
                logging.info('data[%s] = "%s"', key, request[key])
            
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

