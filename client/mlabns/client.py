#! /usr/bin/env python

import ConfigParser
import urllib
import urllib2
from optparse import OptionParser
from os import path
from os import access
from os import R_OK

from mlabns.util import request_validation

import logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.DEBUG)

class BasicClient:
  """The UpdateClient runs on each sliver, monitoring and regularly
  updating the status to GoogleAppEngine. 
  TODO(claudiu): If the configuration file is not passed as an argument,
  the client looks for a default location e.g. '/etc/mlab-ns.conf'.
  """

  def __init__(self):
    self.key = None
    self.server_url = None
    self.requests = []

  def read_configuration(self, config_file):
    """Reads update configuration from file.
    
    The config parameters are specified in the ConfigParser format(e.g):
    [key - used tu sign the updates]
    key: sliver_key
    
    [server_url - url on GAE side where the updates are sent]
    server_url: http://mlab-ns.appspot.com/register
    
    [tool-1]
    sliver_id: npad.iupui.mlab2.ams01
    slice_id: npad.iupui
    sliver_ipv4: 1.2.3.4
    sliver_ipv6: ::1::2
    tool_sliver_id: npad.iupui.mlab2.ams01
    url:  http://npad.iupui.mlab2.ams01.measurement-lab.org:8000
        
    ....

    [tool-N]
    sliver_id: npad.iupui.mlab2.ams01
    slice_id: npad.iupui
    sliver_ipv4: 1.2.3.4
    sliver_ipv6: ::1::2
    tool_sliver_id: npad.iupui.mlab2.ams01
    url:  http://npad.iupui.mlab2.ams01.measurement-lab.org:9000

    Args:
      config_file: A file containing the data configuration.
    """
    config = ConfigParser.ConfigParser()
    try:
      config.read(config_file)
    except ConfigParser.Error, e:
      # TODO(Claudiu) Log the error and trigger an event/notification.
      logging.error('Cannot read the configuration file: %s.', e)
      exit(-1)
 
    for section in config.sections():
      if section == 'key':
        self.key = config.get(section, 'key')
      elif section == 'server_url':
        self.server_url = config.get(section, 'server_url')
      else:
        logging.info('START %s', section)
        request = {}
        for option in config.options(section):
          request[option] = config.get(section, option)
          logging.info('%s = "%s"', option, config.get(section, option))    
        logging.info('END %s\n.', section)

        self.configure_request(request)
        request['timestamp'] = request_validation.generate_timestamp()
        signature = request_validation.sign(request, self.key)
        request['sign'] = signature
        self.requests.append(request)
    if self.key is None or self.server_url is None:
      logging.error('Missing key or server_url.')
      exit(-1)

  def configure_request(self, request):
    """Custom setup to be implemented in subclasses.

    Args:
      request: A dict containing the data to be sent to the server. Any 
      changes or checking before sending the data must be implemented in
      this method.
    """
    pass

  def handle_error(self, error):
    """Custom error handling to be implemented in subclasses.

    Args:
      error: urllib2.URLError raised if the send fails.
    """
    pass

  def send_requests(self):
    """Sends the requests to the server."""

    url = self.server_url
    
    for request in self.requests:
      data = urllib.urlencode(request)
      req = urllib2.Request(url, data)
      logging.info('Request:')
      for key in request.keys():
        logging.info('data[%s] = "%s"', key, request[key])
     
      logging.info('Sending...\n')
      try:
        response = urllib2.urlopen(req)
        logging.info('Response: %s\n', response.read())
      except urllib2.URLError, e:
        # TODO(Claudiu) log the error and trigger an event/notification
        # based on the HTTP error code.
        logging.error('Cannot send request: %s.\n', e)

  def run(self):
    parser = OptionParser()
    parser.add_option(
      '-f',
      '--file',
      dest='filename',
      help='configuration file')
  
    (options, args) = parser.parse_args()
    if options.filename is None:
      # TODO(Claudiu) log the error and trigger an event/notification.
      logging.error('Missing configuration file.')
      parser.print_help()
      exit(-1)
  
    config_file = options.filename  
    if  not path.exists(config_file):
      # TODO(Claudiu) log the error and trigger an event/notification.
      logging.error('%s does not exist.', config_file)
      exit(-1)
  
    if not path.isfile(config_file):
      # TODO(Claudiu) log the error and trigger an event/notification.
      logging.error('%s is not a file.', config_file)
      exit(-1)
     
    if not access(config_file, R_OK):
      # TODO(claudiu) log the error and trigger an event/notification.
      logging.error('Cannot read %s.', config_file)
      exit(-1)

    self.read_configuration(config_file)
    self.send_requests()
