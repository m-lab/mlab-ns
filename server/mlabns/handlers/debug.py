from django.utils import simplejson

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from mlabns.db import model
from mlabns.util import constants
from mlabns.util  import util
from mlabns.util import message
from mlabns.util import resolver

import logging

class DebugHandler(webapp.RequestHandler):
    """Returns info of the server this client would be redirected to."""

    def post(self):
        """Not implemented."""
        return util.send_not_found(self)

    def get(self):
        """Handles an HTTP GET request.

        Returns the server where the user would be redirected
        if a lookup request was made from this IP address.
        """
        parts = self.request.path.strip('/').split('/')
        lookup_query = resolver.LookupQuery()

        ip_address = self.request.get(message.REMOTE_ADDRESS)
        if ip_address:
            dictionary = {}
            for argument in self.request.arguments():
                dictionary[argument] = self.request.get(argument)
            lookup_query.initialize_from_dictionary(dictionary)
        else:
            lookup_query.initialize_from_http_request(self.request)

        lookup_query.tool_id = parts[1]
        geo_resolver = resolver.GeoResolver()
        destination = geo_resolver.answer_query(lookup_query)

        if destination is None:
            return util.send_not_found(self)

        sliver_tools = geo_resolver.get_sliver_tool_candidates(
            lookup_query)
        sites  =[]
        for sliver_tool in sliver_tools:
            site = model.Site.get_by_key_name(sliver_tool.site_id)
            sites.append(site)

        return self.send_map_view(destination, lookup_query, sites)

    def send_map_view(self, sliver_tool, lookup_query, sites):
        # Destination site.
        site = model.Site.get_by_key_name(sliver_tool.site_id)
        if site is None:
            return self.send_html_view(sliver_tool)

        destination_site = {}
        destination_site['site_id'] = site.site_id
        destination_site['city'] = site.city
        destination_site['country'] = site.country
        destination_site['latitude'] = site.latitude
        destination_site['longitude'] = site.longitude
        url_info = '';
        if sliver_tool.http_port != 'off':
            url = '' .join([
                'http://', sliver_tool.fqdn_ipv4, ':', sliver_tool.http_port])
            url_info = ''.join([
                '<a class="footer" href=', url,'>', url,'</a>'])

        logging.info('URL: %s', url_info)
        destination_site['info'] = ''.join([
            '<div id=siteShortInfo>',
            '<h2>',
            site.city, ',', site.country,
            '</h2>',
            url_info,
            '</div>'])

        # Get the list af all other sites.
        site_list = []
        for site in sites:
            if site.site_id != destination_site['site_id']:
                record = {}
                record['site_id'] = site.site_id
                record['city'] = site.city
                record['country'] = site.country
                record['latitude'] = site.latitude
                record['longitude'] = site.longitude
                site_list.append(record)

        user_info = {}
        user_info['city'] = lookup_query.city
        user_info['country'] = lookup_query.country
        user_info['latitude'] = lookup_query.latitude
        user_info['longitude'] = lookup_query.longitude

        site_list_json = simplejson.dumps(site_list)
        destination_site_json = simplejson.dumps(destination_site)
        user_info_json = simplejson.dumps(user_info)

        self.response.out.write(
            template.render('mlabns/templates/lookup_map.html', {
                'sites' : site_list_json,
                'user' : user_info_json,
                'destination' : destination_site_json }))
