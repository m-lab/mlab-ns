from google.appengine.ext import db
from google.appengine.ext import webapp

from mlabns.db import model
from mlabns.util import message
from mlabns.util import util

import json
import logging
import time

class CleanupHandler(webapp.RequestHandler):
    """Deletes old pings to keep the datastore under control."""

    def get(self):
      """Perform the cleanup."""
      # get all rows that are older than 24 hours.
      start = float(time.time() - (60 * 60 * 24));
      logging.info('Deleting pings since %.2f', start);
      q = db.GqlQuery('SELECT * FROM Ping WHERE time < ' + start)
      results = q.fetch(100)
      while results:
          db.delete(results)
          results = q.fetch(100)

class PingsHandler(webapp.RequestHandler):
    """Returns batches of recent queries for visualization."""

    def get(self):
        """Handles an HTTP GET request.

        The URL must be in the following format:
        'http://mlab-ns.appspot.com/pings?tool_id=..&address_family=..',
        where tool_id is one of the tools running on M-Lab.
        """
        tool_id = self.request.get(message.TOOL_ID)
        if tool_id == '':
          util.send_server_error(self.request)
          return

        address_family = self.request.get(message.ADDRESS_FAMILY)
        if address_family == '':
          util.send_server_error(self.request)
          return

        last_time = float(self.request.get('last_time', 0))
        logging.info('Getting pings for %s|%s from %f', tool_id,
                      address_family, last_time)

        q = model.Ping.all()
        if tool_id != 'all':
          q.filter("tool_id =", tool_id)
        q.filter("address_family =", address_family)
        q.filter("time >", last_time)
        q.order("-time")

        pings = []
        for p in q.run():
          pings.append({
              'latitude' : p.latitude,
              'longitude' : p.longitude,
              'time' : p.time
              })

        logging.info('Found %d pings', len(pings))

        json_data = json.dumps(pings)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_data)

    def post(self):
        """Not implemented."""
        return util.send_not_found(self)
