from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.util import message
from mlabns.util import registration_message
from mlabns.db import model
from mlabns.util import error

import logging

class RegistrationHandler(webapp.RequestHandler):
    """Handles SliverTools registrations.

    All the registrations come as HTTP POST requests and must be signed.
    """

    def get(self):
        """Not implemented."""
        return error.not_found(self)

    def post(self):
        """Handles registrations through HTTP POST requests.

        Verify the request and if valid, add a new record to the
        corresponding db.
        """
        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument)

        entity = self.request.get(message.ENTITY)
        if entity == message.ENTITY_SITE:
            return self.register_site(dictionary)
        if entity == message.ENTITY_SLIVER_TOOL:
            return self.register_sliver_tool(dictionary)

        logging.error('Unknow entity %s', entity)
        for item in dictionary:
            logging.info('data[%s] = %s', item, dictionary[item])

        return error.not_found(self)

    def register_site(self, dictionary):
        registration = registration_message.SiteRegistrationMessage()
        try:
            registration.initialize_from_dictionary(dictionary)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return error.not_found(self)

        # TODO (claudiu) Change with login.
        key = 'mlab-ns@admin'
        if not registration.verify_signature(key):
            logging.error('Bad signature')
            for item in dictionary:
                logging.info('data[%s] = %s', item, dictionary[item])
            return error.not_found(self)

        try:
            lat, lon = [float(x) for x in registration.lat_long.split(',')]
        except ValueError:
            logging.error('Bad geo coordinates %s', registration.lat_long)
            return error.not_found(self)

        site = model.Site(
            site_id=registration.site_id,
            city=registration.city,
            country=registration.country,
            latitude=lat,
            longitude=lon,
            metro=registration.metro.split(','),
            key_name=registration.site_id)

        site.put()
        return self.success()

    def register_sliver_tool(self, dictionary):
        registration = registration_message.SliverToolRegistrationMessage()
        try:
            registration.initialize_from_dictionary(dictionary)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return error.not_found(self)

        # TODO (claudiu) Change with login.
        key = 'mlab-ns@admin'
        if not registration.verify_signature(key):
            logging.error('Bad signature')
            return error.not_found(self)

        sliver_tool_id = model.get_sliver_tool_id(registration)

        # Add lat/long info from the site db.
        site = model.Site.get_by_key_name(registration.site_id)
        if not site:
            logging.error('No site found for this sliver tool.')
            return error.not_found(self)

        sliver_tool = model.SliverTool(
            tool_id=registration.tool_id,
            slice_id=registration.slice_id,
            site_id=registration.site_id,
            server_id=registration.server_id,
            sliver_tool_key=registration.sliver_tool_key,
            sliver_ipv4=registration.sliver_ipv4,
            sliver_ipv6=registration.sliver_ipv6,
            url=registration.url,
            status=registration.status,
            latitude=site.latitude,
            longitude=site.longitude,
            key_name=sliver_tool_id)

        sliver_tool.put()
        return self.success()

    def success(self, message='200 OK'):
        self.response.out.write(message)
