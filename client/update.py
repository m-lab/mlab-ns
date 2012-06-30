#! /usr/bin/env python

# The design documentation can be found at http://goo.gl/48S22.

import ConfigParser
import logging
import urllib
import urllib2
from optparse import OptionParser
from os import R_OK
from os import access
from os import path

from mlabns import flags
from mlabns import message
from mlabns import util

class UpdateClient:
    """Sends SliverTool status updates to the GAE server."""
    
    def __init__(self):
        # String representing the key used to sign the updates.
        self.sliver_tool_key = None

        # String that represents the URL where the updates are sent.
        self.server_url = None

        # List of the updates to be sent to the server.
        self.updates = []
        
    def read_configuration(self, config_file):
        """Reads SliverTool configuration from file.
        
        The config parameters are specified in the ConfigParser format
        (see http://docs.python.org/library/configparser.html).
        'config_file' usually contains the configuration of a single 
        SliverTool. However, it's possible to have the configurations of
        more that one SliverTool in the same file. See example of 
        configuration below.
        
        [server_url]
        server_url: http://localhost:8080/update
        
        [npad.iupui.mlab1.ath01.measurement-lab.org]
        tool_id: npad
        node_id: mlab1.ath01.measurement-lab.org
        sliver_tool_id:	npad.iupui.mlab1.ath01.measurement-lab.org
        sliver_tool_key: npad.iupui.key
        sliver_ipv4: 83.212.4.12
        sliver_ipv6: off 
        url: http://npad.iupui.mlab1.ath01.measurement-lab.org:8000
        ...
        [npad.iupui.mlab1.atl01.measurement-lab.org]
        tool_id: npad
        node_id: mlab1.atl01.measurement-lab.org
        sliver_tool_id:	npad.iupui.mlab1.atl01.measurement-lab.org
        sliver_tool_key: npad.iupui.key
        sliver_ipv4: 4.71.254.138
        sliver_ipv6: off 
        url: http://npad.iupui.mlab1.atl01.measurement-lab.org:8000
        
        Args:
          config_file: A string that represents the name of a file.
        
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
            if section == flags.SECTION_KEY:
                self.sliver_tool_key = config.get(section, flags.OPTION_KEY)
            elif section == flags.SECTION_URL:
                self.server_url = config.get(section, flags.OPTION_URL)
            else:
                if self.sliver_tool_key is None:
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
                
                self.update_status(update)
                update[message.TIMESTAMP] = util.generate_timestamp()
                signature = util.sign(update, self.sliver_tool_key)
                update[message.SIGNATURE] = signature
                self.updates.append(update)
        
        return True
    
    def send_updates(self):
        """Sends the updates to the server."""
        
        for update in self.updates:
            data = urllib.urlencode(update)
            request = urllib2.Request(self.server_url, data)
            logging.info('Sending request:')
            for key in update.keys():
                logging.info('data[%s] = "%s"', key, update[key])
            try:
                response = urllib2.urlopen(request)
                logging.info('Response: %s\n', response.read())
            except urllib2.URLError, e:
                # TODO(claudiu) Trigger an event/notification.
                logging.error('Cannot send request: %s.\n', e)
    
    def update_status(self, update):
        """Updates the status of a given tool running on the sliver.
        
        Args:
            update: A dict containing the data to be sent to the server.
        """
        
        if not update.has_key('sliver_tool_id'):
            logging.error('Bad upate: "sliver_tool_id" not found.')
        elif not update.has_key('status'):
            logging.error('Bad update: "status" not found.')
        else:
            # TODO(claudiu) Add a tool-specific implementation based
            # on the PlanetLab API.
            update[message.STATUS] = message.STATUS_ONLINE

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
    
    client = UpdateClient()
    if not client.read_configuration(config_file):
        logging.error('Cannot read file %s.', config_file)
        exit(-1)
    
    client.send_updates()
    
if __name__ == '__main__':
    main() 
