#! /usr/bin/env python

# TODO (claudiu) Add link to doc that describes the design of the
# application.

import ConfigParser
import logging
from optparse import OptionParser
from os import access
from os import path
from os import R_OK
import time
import urllib
import urllib2

from mlabns.util import message
from mlabns.util import sign

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
            registration = {}
            for option in config.options(section):
                registration[option] = config.get(section, option)
                logging.info('%s = "%s"', option, registration[option])
            logging.info('END %s\n.', section)
            
            registration[message.TIMESTAMP] = str(int(time.time()))
            registration[message.SIGNATURE] = sign.sign_message(
                registration,
                admin_key)
            self.registrations.append(registration)
        
        return True
    
    def send_requests(self):
        """Sends the registration requests to the server."""
        
        for registration in self.registrations:
            data = urllib.urlencode(registration)
            request = urllib2.Request(self.server_url, data)
            logging.info('Sending request:')
            for key in registration.keys():
                logging.info('data[%s] = "%s"', key, registration[key])
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
