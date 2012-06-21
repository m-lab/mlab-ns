#! /usr/bin/env python

import urllib
import urllib2

import logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.DEBUG)

from mlabns import client

class UpdateClient(client.BasicClient):
  """The UpdateClient runs on each sliver, monitoring and regularly
  updating the status to GoogleAppEngine. 
  """

  def check_status(self, sliver_tool_id):
    """Checks the status of a given tool running on the sliver
    
    Args:
      sliver_tool_id: Id that uniquely identifies an instance of a tool
      running on the sliver.

    # TODO(claudiu) Tool-specific implementation this based on the
    # PlanetLab available API.
    
    Returns:
      A string describing the status of the tool: 'online' and 'offline' are
      currently supported.
    """
    return 'online'

  def configure_request(self, request):
    """Custom configuration specific for the UpdateClient.
    
    Args:
      request: A dict containing the data to be sent to the server. The 
      UpdateClient makes sure the 'status' field is updated before sending
      the data to the server.
    """
    if not request.has_key('sliver_tool_id'):
      logging.error('Unknown request: "sliver_tool_id" key not found.')
      exit(-1)
    elif not request.has_key('status'):
      logging.error('Unknown request: "status" key not found.')
      exit(-1)

    request['status'] = self.check_status(request)

  def handle_error(self, error):
    """Custom error handling.
    
    TODO(claudiu) Trigger events/notifications based on the type of the error.
    
    Args:
      error: urllib2.URLError raised if the send fails.
    """
    pass

def main():
  client = UpdateClient()
  client.run()  

if __name__ == '__main__':
  main() 
