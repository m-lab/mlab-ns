#! /usr/bin/env python

import urllib
import urllib2

import logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.DEBUG)

from mlabns import client

class RegistrationClient(client.BasicClient):
  """Registers one or more tools running on the sliver. This class is meant to
  be used only for debugging purposes since it doesn't support currently user
  authentication.
  TODO(claudiu) Add login support.
  """

  def handle_error(self, error):
    # TODO(Claudiu) Trigger an event/notification.
    pass

def main():
  client = RegistrationClient()
  client.run()  

if __name__ == '__main__':
  main()
