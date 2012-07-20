from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import logging
import time

from mlabns.db import model
from mlabns.util import message
from mlabns.util import update_message

class UpdateHandler(webapp.RequestHandler):
    """Handles SliverTools updates."""

    def get(self):
        # Not implemented.
        self.send_not_found()

    def post(self):
        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument)

        update = update_message.UpdateMessage()
        try:
            update.initialize_from_dictionary(dictionary)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return self.send_not_found()

        # Move this in db.model.py.
        sliver_tool_id = model.get_sliver_tool_id(update)
        sliver_tool = model.SliverTool.get_by_key_name(sliver_tool_id)

        if sliver_tool is None:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Unknown sliver_tool_id %s.', sliver_tool_id)
            return self.send_not_found()

        if not update.verify_signature(sliver_tool.sliver_tool_key):
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Bad signature from %s.', sliver_tool_id)
            return self.send_not_found()

        # Prevent reply attacks.
        if (update.timestamp <= sliver_tool.update_request_timestamp):
            logging.error('Old timestamp from %s.', sliver_tool_id)
            return self.send_not_found()

        # TODO(claudiu) Monitor and log changes in the parameters.
        # TODO(claudiu) Trigger an event or notification.
        sliver_tool.status = update.status
        sliver_tool.sliver_ipv4 = update.sliver_ipv4
        sliver_tool.sliver_ipv6 = update.sliver_ipv6
        sliver_tool.url = update.url
        sliver_tool.update_request_timestamp = long(time.time())

        # Write changes to db.
        sliver_tool.put()
        self.send_success()

    def send_error(self, error_code=404):
        # 404: Not found.
        self.error(error_code)
        self.response.out.write('Not found')

    def send_not_found(self):
        self.error(404)
        self.response.out.write(
            template.render('mlabns/templates/not_found.html', {}))

    def send_success(self):
        self.response.out.write('200 OK')
