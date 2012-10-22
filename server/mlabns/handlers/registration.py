from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from Crypto.Cipher import DES
from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import registration_message
from mlabns.util import util

import codecs
import logging
import time

class RegistrationHandler(webapp.RequestHandler):
    """Handles SliverTools registrations.

    All the registrations come as HTTP POST requests and must be signed.
    """

    def get(self):
        """Not implemented."""
        return util.send_not_found(self)

    def post(self):
        """Handles registrations through HTTP POST requests.

        Decrypt the request and, if valid, add a new record to the
        corresponding db.
        """
        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument, default_value=None)
            logging.info('data[%s] = %s',
                argument, dictionary[argument])

        key_entry = model.EncryptionKey.get_by_key_name(
            constants.REGISTRATION_KEY_ID)
        if not key_entry:
            logging.error('Registration key not found.')
            return util.send_not_found(self)

        entity = self.request.get(message.ENTITY, default_value=None)
        if entity == message.ENTITY_SITE:
            return self.register_site(
                dictionary, key_entry.encryption_key)
        if entity == message.ENTITY_SLIVER_TOOL:
            return self.register_sliver_tool(
                dictionary, key_entry.encryption_key)

        logging.error('Unknow entity %s', entity)
        for item in dictionary:
            logging.error('data[%s] = %s', item, dictionary[item])

        return util.send_not_found(self)

    def register_site(self, dictionary, encryption_key):
        registration = registration_message.SiteRegistrationMessage()
        try:
            registration.decrypt_message(dictionary, encryption_key)
        except message.DecryptionError, e:
            logging.error('Decryption error: %s', e)
            return util.send_not_found(self)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return util.send_not_found(self)

        try:
            lat, lon = [float(x) for x in registration.lat_long.split(',')]
        except ValueError:
            logging.error('Bad geo coordinates %s', registration.lat_long)
            return util.send_not_found(self)

        site = model.Site(
            site_id=registration.site_id,
            city=registration.city,
            country=registration.country,
            latitude=lat,
            longitude=lon,
            metro=registration.metro.split(','),
            registration_timestamp=long(time.time()),
            key_name=registration.site_id)

        try:
            site.put()
        except TransactionFailedError:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Failed to write changes to db.')
            return util.send_server_error(self)

        # Update memcache with map: metro -> site IDs.
        for metro in registration.metro.split(','):
            sites = memcache.get(
                metro, namespace=constants.MEMCACHE_NAMESPACE_METROS)
            if sites is None:
                sites = []
            sites.append(registration.site_id)
            if not memcache.set(metro, sites,
                                namespace=constants.MEMCACHE_NAMESPACE_METROS):
                logging.error('Memcache set failed')

        return util.send_success(self)

    def register_sliver_tool(self, dictionary, encryption_key):
        registration = registration_message.SliverToolRegistrationMessage()
        try:
            registration.decrypt_message(dictionary, encryption_key)
        except message.DecryptionError, e:
            logging.error('Decryption error: %s', e)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return util.send_not_found(self)

        sliver_tool_id = model.get_sliver_tool_id(
            registration.tool_id,
            registration.slice_id,
            registration.server_id,
            registration.site_id)

        # Get lat/long info from the site db.
        site = model.Site.get_by_key_name(registration.site_id)
        if not site:
            logging.error(
                'SliverTool site %s was not found in the db.',
                registration.site_id)
            return util.send_not_found(self)
        timestamp=long(time.time())
        sliver_tool = model.SliverTool(
            tool_id=registration.tool_id,
            slice_id=registration.slice_id,
            site_id=registration.site_id,
            server_id=registration.server_id,
            fqdn_ipv4=registration.fqdn_ipv4,
            fqdn_ipv6=registration.fqdn_ipv6,
            server_port=registration.server_port,
            http_port=registration.http_port,
            sliver_ipv4=registration.sliver_ipv4,
            sliver_ipv6=registration.sliver_ipv6,
            status_ipv4=registration.status_ipv4,
            status_ipv6=registration.status_ipv6,
            latitude=site.latitude,
            longitude=site.longitude,
            city=site.city,
            country=site.country,
            update_request_timestamp=timestamp,
            key_name=sliver_tool_id)

        try:
            sliver_tool.put()
        except TransactionFailedError:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Failed to write changes to db.')
            return util.send_server_error(self)

        return util.send_success(self)
