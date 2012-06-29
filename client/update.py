#! /usr/bin/env python

import ConfigParser
import logging
from optparse import OptionParser
from os import path
from os import access
from os import R_OK
import urllib
import urllib2

from mlabns.util import constants
from mlabns.util import request_validation

class UpdateClient:
    """Sends SliverTool status updates to the GAE server."""

    def __init__(self):
        self.key = None
        self.server_url = None
        self.updates = []
        logging.basicConfig(
            format='[%(asctime)s] %(levelname)s: %(message)s',
            level=logging.DEBUG)

    def read_configuration(self, config_file):
        """Reads update configuration from file.

        The config parameters are specified in the ConfigParser format.
        Normally  there is only one SliverTool to be updated, but this
        example is for the generic case, where multiple tools are
        running on the same sliver, therefore using different ports:

        [server_url]
        server_url: http://localhost:8080/update

        [key]
        key: npad.iupui.key

        [npad.iupui.mlab0.lhr01]
        node_id: mlab0.lhr01.measurement-lab.org
        tool_id: npad
        sliver_tool_id: npad.iupui.mlab0.lhr01
        sliver_ipv4: 1.1.1.1
        sliver_ipv6: :1::1::1::1
        url:  http://npad.iupui.mlab0.lhr01.measurement-lab.org:8000
        status: online
        
        ...

        [ndt.mlab0.lhr01]
        node_id: mlab0.lhr01.measurement-lab.org
        tool_id: npad
        sliver_tool_id: ndt.mlab0.lhr01
        sliver_ipv4: 1.1.1.1
        sliver_ipv6: :1::1::1::1
        url:  http://ndt.mlab0.lhr01.measurement-lab.org:9000
        status: online
   
        Args:
          config_file: A file containing the data configuration.

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
            if section == 'key':
                self.key = config.get(section, 'key')
            elif section == 'server_url':
                self.server_url = config.get(section, 'server_url')
            else:
                logging.info('BEGIN %s', section)
                update = {}
                for option in config.options(section):
                    update[option] = config.get(section, option)
                    logging.info(
                        '%s = "%s"',
                        option,
                        config.get(section, option))    
                logging.info('END %s\n.', section)

                self.update_status(update)
                update['timestamp'] = request_validation.generate_timestamp()
                signature = request_validation.sign(update, self.key)
                update['sign'] = signature
                self.updates.append(update)

        if self.key is None or self.server_url is None:
            logging.error('Missing key or server_url.')
            return False
        
        return True

    def send_updates(self):
        """Sends the updates to the server."""

        url = self.server_url

        for update in self.updates:
            data = urllib.urlencode(update)
            req = urllib2.Request(url, data)
            logging.info('Request:')
            for key in update.keys():
                logging.info('data[%s] = "%s"', key, update[key])
            
            logging.info('Sending...\n')
            try:
                response = urllib2.urlopen(req)
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
            # TODO(claudiu) Tool-specific implementation based on the
            # PlanetLab API.
            update['status'] = constants.STATUS_ONLINE

def main():
    parser = OptionParser()
    parser.add_option(
    '-f',
    '--file',
    dest='filename',
    help='configuration file')

    (options, args) = parser.parse_args()
    if options.filename is None:
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Missing configuration file.')
        parser.print_help()
        exit(-1)

    config_file = options.filename  
    if  not path.exists(config_file):
        # TODO(claudiu) Trigger an event/notification.
        logging.error('%s does not exist.', config_file)
        exit(-1)

    if not path.isfile(config_file):
        # TODO(claudiu) Trigger an event/notification.
        logging.error('%s is not a file.', config_file)
        exit(-1)
 
    if not access(config_file, R_OK):
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Cannot read %s.', config_file)
        exit(-1)

    client = UpdateClient()
    if not client.read_configuration(config_file):
        logging.error('Cannot read %s.', config_file)
        exit(-1)

    client.send_updates()

if __name__ == '__main__':
    main() 
