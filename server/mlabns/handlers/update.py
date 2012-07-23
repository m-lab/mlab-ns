from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import logging
import time

from mlabns.db import model
from mlabns.util import message
from mlabns.util import update_message
from mlabns.util import error

class UpdateHandler(webapp.RequestHandler):
    """Handles SliverTools updates."""

    def get(self):
        # Not implemented.
        return error.not_found(self)

    def post(self):
        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument)

        update = update_message.UpdateMessage()
        try:
            update.initialize_from_dictionary(dictionary)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return error.not_found(self)

        sliver_tool_id = model.get_sliver_tool_id(
            update.tool_id,
            update.slice_id,
            update.server_id,
            update.site_id)
        sliver_tool = model.SliverTool.get_by_key_name(sliver_tool_id)

        if sliver_tool is None:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Unknown sliver_tool_id %s.', sliver_tool_id)
            return error.not_found(self)

        if not update.verify_signature(sliver_tool.sliver_tool_key):
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Bad signature from %s.', sliver_tool_id)
            return error.not_found(self)

        # Prevent reply attacks.
        if (update.timestamp <= sliver_tool.update_request_timestamp):
            logging.error(
                'Timestamp in update %s is older than value in db (%s)',
                sliver_tool_id, sliver_tool.update_request_timestamp)
            return error.not_found(self)

        # TODO(claudiu) Monitor and log changes in the parameters.
        # TODO(claudiu) Trigger an event or notification.
        sliver_tool.status = update.status
        sliver_tool.sliver_ipv4 = update.sliver_ipv4
        sliver_tool.sliver_ipv6 = update.sliver_ipv6
        sliver_tool.url = update.url
        sliver_tool.update_request_timestamp = long(time.time())

        # Write changes to db.
        try:
            sliver_tool.put()
        except TransactionFailedError:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Failed to write changes to db.')

        return self.success()

    def success(self):
        self.response.out.write('200 OK')
