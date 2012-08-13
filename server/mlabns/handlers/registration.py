from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from Crypto.Cipher import DES
from mlabns.db import model
from mlabns.util import message
from mlabns.util import registration_message
from mlabns.util import util

import logging
import codecs

class RegistrationHandler(webapp.RequestHandler):
    """Handles SliverTools registrations.

    All the registrations come as HTTP POST requests and must be signed.
    """

    def get(self):
        """Not implemented."""

        if self.request.path != '/register/sites_from_file':
            return util.send_not_found(self)

        block_number = self.request.get('block_number')

        prefix = 'mlabns/util/tmp/site_block'
        filename = '.'.join([prefix, block_number])

        keys = [
            'location_id',
            'country',
            'region',
            'city',
            'postal_code',
            'latitude',
            'longitude',
            'metro_code',
            'area_code'
        ]

        # Add to db.
        for line in open(filename, 'r').readlines():
            values = line.split(',')

            location = dict(zip(keys, values))
            location['latitude'] = float(location['latitude'])
            location['longitude'] = float(location['longitude'])
            location['region'] = location['region'].decode(
                'utf-8','ignore')
            location['country'] = location['country'].decode(
                'utf-8','ignore')
            location['city'] = location['city'].decode(
                'utf-8','ignore')

            model.GeoLiteCityLocation(
                location_id=location['location_id'],
                country=location['country'],
                region=location['region'],
                city=location['city'],
                latitude=location['latitude'],
                longitude=location['longitude'],
                key_name=location['location_id']).put()

        util.send_success(self)

    def post(self):
        """Handles registrations through HTTP POST requests.

        Decrypt the request and if valid, add a new record to the
        corresponding db.
        """
        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument)
            logging.info('data[%s] = %s',
                argument, dictionary[argument])

        entity = self.request.get(message.ENTITY)
        if entity == message.ENTITY_SITE:
            return self.register_site(dictionary)
        if entity == message.ENTITY_SLIVER_TOOL:
            return self.register_sliver_tool(dictionary)

        logging.error('Unknow entity %s', entity)
        for item in dictionary:
            logging.info('data[%s] = %s', item, dictionary[item])

        return util.send_not_found(self)

    def register_site(self, dictionary):
        admin_key = model.EncryptionKey.get_by_key_name('admin')
        if not admin_key:
            logging.error('Admin key not found.')
            return util.send_not_found(self)
        encryption_key = admin_key.encryption_key

        registration = registration_message.SiteRegistrationMessage()
        try:
            registration.decrypt_message(dictionary, encryption_key)
        except message.DecryptionError, e:
            logging.error('Encryption error: %s', e)
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
            key_name=registration.site_id)

        try:
            site.put()
        except TransactionFailedError:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Failed to write changes to db.')
            return util.send_server_error(self)

        # Update the memcache.
        sites = memcache.get('sites')
        if not sites:
            sites = {}

        sites[site.site_id] = site
        if not memcache.set('sites', sites):
            logging.error('Memcache set failed')

        return util.send_success(self)

    def register_sliver_tool(self, dictionary):
        admin_key = model.EncryptionKey.get_by_key_name('admin')
        if not admin_key:
            logging.error('Admin key not found.')
            return util.send_not_found(self)
        encryption_key = admin_key.encryption_key

        registration = registration_message.SliverToolRegistrationMessage()
        try:
            registration.decrypt_message(dictionary, encryption_key)
        except message.DecryptionError, e:
            logging.error('Encryption error: %s', e)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return util.send_not_found(self)

        sliver_tool_id = model.get_sliver_tool_id(
            registration.tool_id,
            registration.slice_id,
            registration.server_id,
            registration.site_id)

        # Add lat/long info from the site db.
        site = model.Site.get_by_key_name(registration.site_id)
        if not site:
            logging.error(
                'SliverTool site %s was not found in the db.',
                registration.site_id)
            return util.send_not_found(self)

        sliver_tool = model.SliverTool(
            tool_id=registration.tool_id,
            slice_id=registration.slice_id,
            site_id=registration.site_id,
            server_id=registration.server_id,
            fqdn=registration.fqdn,
            server_port=registration.server_port,
            http_port=registration.http_port,
            sliver_tool_key=registration.sliver_tool_key,
            sliver_ipv4=registration.sliver_ipv4,
            sliver_ipv6=registration.sliver_ipv6,
            url=registration.url,
            status=registration.status,
            latitude=site.latitude,
            longitude=site.longitude,
            key_name=sliver_tool_id)

        try:
            sliver_tool.put()
        except TransactionFailedError:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Failed to write changes to db.')
            return util.send_server_error(self)

       # Update the memcache.
        sliver_tools = memcache.get(sliver_tool.tool_id)
        if not sliver_tools:
            sliver_tools = {}

        sliver_tools[sliver_tool_id] = sliver_tool
        if not memcache.set(sliver_tool.tool_id, sliver_tools):
            logging.error('Memcache set failed')

        return util.send_success(self)
