from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.util import message
from mlabns.db import model

import logging

class RegistrationHandler(webapp.RequestHandler):
    """Handles SliverTools registrations.

    All the registrations come as HTTP POST requests and must be signed.
    """

    def get(self):
        """Not implemented."""
        return self.send_not_found()

    def post(self):
        """Handles registrations through HTTP POST requests.

        Verify the request and if valid, add a new record to the
        corresponding db.
        """
        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument)

        registration = message.RegistrationMessage()
        try:
            registration.read_from_dictionary(dictionary)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return self.send_not_found()

        # TODO (claudiu) Change with login.
        key = 'mlab-ns@admin'
        if not registration.verify_signature(key):
            logging.error('Bad signature')
            return self.send_not_found()

        for argument in self.request.arguments():
            logging.info(
                'data[%s] = %s',
                argument,
                self.request.get(argument))

        if registration.is_sliver_tool():
            sliver_tool_id = '-' . join(
                [registration.get_tool_id(),
                registration.get_slice_id(),
                registration.get_server_id(),
                registration.get_site_id()])

            # Add lat/long info from the site db.
            site = model.Site.get_by_key_name(registration.get_site_id())
            if not site:
                logging.error('No site found for this sliver tool.')
                return self.send_not_found()

            sliver_tool = model.SliverTool(
                tool_id=registration.get_tool_id(),
                slice_id=registration.get_slice_id(),
                site_id=registration.get_site_id(),
                server_id=registration.get_server_id(),
                sliver_tool_key=registration.get_sliver_tool_key(),
                sliver_ipv4=registration.get_sliver_ipv4(),
                sliver_ipv6=registration.get_sliver_ipv6(),
                url=registration.get_url(),
                status=registration.get_status(),
                lat_long=site.lat_long,
                key_name=sliver_tool_id)
            sliver_tool.put()
            self.send_success()
        elif registration.is_site():
            site = model.Site(
                site_id=registration.get_site_id(),
                city=registration.get_city(),
                country=registration.get_country(),
                lat_long=registration.get_lat_long(),
                metro=registration.get_metro().split(','),
                key_name=registration.get_site_id())
            site.put()
            self.send_success()
        else:
            self.send_not_found()

    def send_success(self, message='200 OK'):
        self.response.out.write(message)

    def send_error(self, error_code=404, message='Not found'):
        # 404: Not found.
        self.error(error_code)
        self.response.out.write(message)

    def send_not_found(self):
        self.error(404)
        self.response.out.write(
        template.render('mlabns/templates/not_found.html', {}))
