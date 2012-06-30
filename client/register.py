#! /usr/bin/env python

# TODO (claudiu) Add link to doc that describes the design of the
# application.

import ConfigParser
import logging
from optparse import OptionParser
from os import access
from os import path
from os import R_OK
import urllib
import urllib2

from mlabns import message
from mlabns import util
from mlabns import flags

class RegistrationClient:
    """Registers SliverTools with the GAE server."""
    
    def __init__(self):
        # TODO (claudiu) Add comments for each instance var.
        self.admin_key = None
        self.server_url = None
        self.registrations = []
        
    def read_configuration(self, config_file):
        """Reads SliverTools configuration from file.
        
        The config parameters are specified in the ConfigParser format.
        See example of configuration below.
        
        [server_url]
        server_url: http://localhost:8080/register
        
        [key]
        key: mlab-ns@admin
        
        [npad.iupui.mlab1.ath01.measurement-lab.org]
        entity: sliver_tool
        tool_id:	npad
        node_id: mlab1.ath01.measurement-lab.org
        sliver_tool_id:	npad.iupui.mlab1.ath01.measurement-lab.org
        sliver_tool_key: npad.iupui.key
        sliver_ipv4: 83.212.4.12
        sliver_ipv6: off 
        url: http://npad.iupui.mlab1.ath01.measurement-lab.org:8000
        status: init
        ...
        
        [npad.iupui.mlab1.atl01.measurement-lab.org]
        entity: sliver_tool
        tool_id:	npad
        node_id: mlab1.atl01.measurement-lab.org
        sliver_tool_id:	npad.iupui.mlab1.atl01.measurement-lab.org
        sliver_tool_key: npad.iupui.key
        sliver_ipv4: 4.71.254.138
        sliver_ipv6: off 
        url: http://npad.iupui.mlab1.atl01.measurement-lab.org:800
        status: init
        
        Return:
            True if no error is encountered, False otherwise.
        """
        config = ConfigParser.ConfigParser()
        try:
            config.read(config_file)
            # TODO(claudiu): If the configuration file is not passed 
            # as an argument use a default location e.g.'/etc/mlab-ns.conf'.
        except ConfigParser.Error, e:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Cannot read the configuration file: %s.', e)
            return False
            
        for section in config.sections():
            print flags.SECTION_KEY
            print flags.OPTION_KEY
            print flags.SECTION_URL
            print flags.OPTION_URL
            if section == flags.SECTION_KEY:
                self.admin_key = config.get(section, flags.OPTION_KEY)
            elif section == flags.SECTION_URL:
                self.server_url = config.get(section, flags.OPTION_URL)
            else:
                if self.admin_key is None:
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
                
                registration[message.TIMESTAMP] = util.generate_timestamp()
                signature = util.sign(registration, self.admin_key)
                registration[message.SIGNATURE] = signature
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
    
    flags.SECTION_KEY = options.section_key
    flags.OPTION_KEY = options.option_key
    flags.SECTION_URL = options.section_url
    flags.OPTION_URL = options.option_url
    
    client = RegistrationClient()
    if not client.read_configuration(config_file):
        logging.error('Cannot read file %s.', config_file)
        exit(-1)
    
    client.send_requests()
    
if __name__ == '__main__':
    main()
