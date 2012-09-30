from django.utils import simplejson

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import resolver
from mlabns.util import util

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

        valid_paths = [
            '/geo/glasnost',
            '/geo/neubot',
            '/geo/ndt',
            '/geo/npad' ]
        if path not in valid_paths:
            return util.send_not_found(self)

        query = resolver.LookupQuery()

        ip_address = self.request.get(message.REMOTE_ADDRESS)
        if ip_address:
            dictionary = {}
            for argument in self.request.arguments():
                dictionary[argument] = self.request.get(argument)
            query.initialize_from_dictionary(dictionary)
        else:
            query.initialize_from_http_request(self.request)

        path = self.request.path.rstrip('/')
        path_parts = self.request.path.strip('/').split('/')
        query.tool_id = path_parts[1]

        debug_resolver = None
        if query.policy == message.POLICY_METRO:
            debug_resolver = resolver.MetroResolver()
        elif query.policy == message.POLICY_GEO:
            debug_resolver = resolver.GeoResolver()
        elif query.policy == message.POLICY_RANDOM:
            debug_resolver = resolver.RandomResolver()
        if debug_resolver is None:
            return util.send_not_found(self)

        destination_sliver_tool = debug_resolver.answer_query(query)
        if destination_sliver_tool is None:
            return util.send_not_found(self)
        candidate_sites = debug_resolver.get_candidates(query)

        sites = model.Site.all().fetch(constants.MAX_FETCHED_RESULTS)
        return self.send_map_view(destination_sliver_tool, query, sites)

    def send_map_view(self, destination_sliver_tool, lookup_query, sites):
        """Displays the map with the user location and the destination site.

        Args:
            destination_sliver_tool: A SliverTool instance. Details about the
                sliver tool are displayed in an info window associated to the
                sliver_tool's site marker.
            lookup_query: A LookupQuery instance.
            site: A Site instance, used to draw a marker on the map.
        """
        destination_site = model.Site.get_by_key_name(destination_sliver_tool.site_id)
        if destination_site is None:
            return self.send_html_view(destination_sliver_tool)

        destination_site_dict = {}
        destination_site_dict['site_id'] = destination_site.site_id
        destination_site_dict['city'] = destination_site.city
        destination_site_dict['country'] = destination_site.country
        destination_site_dict['latitude'] = destination_site.latitude
        destination_site_dict['longitude'] = destination_site.longitude
        url_info = '';
        if destination_sliver_tool.http_port != 'off':
            url = '' .join([
                'http://', sliver_tool.fqdn_ipv4, ':', sliver_tool.http_port])
            url_info = ''.join([
                '<a class="footer" href=', url,'>', url,'</a>'])
        logging.info('URL: %s', url_info)
        destination_site_dict['info'] = ''.join([
            '<div id=siteShortInfo>',
            '<h2>',
            site.city, ', ', site.country,
            '</h2>',
            url_info,
            '</div>'])

        # Get the list af all other sites.
        site_list = []
        for site in sites:
            if site.site_id == destination_site.site_id:
                continue
            site_dict = {}
            site_dict['site_id'] = site.site_id
            site_dict['city'] = site.city
            site_dict['country'] = site.country
            site_dict['latitude'] = site.latitude
            site_dict['longitude'] = site.longitude
            site_list.append(site_dict)

        user_info = {}
        user_info['city'] = lookup_query.city
        user_info['country'] = lookup_query.country
        user_info['latitude'] = lookup_query.latitude
        user_info['longitude'] = lookup_query.longitude

        site_list_json = simplejson.dumps(site_list)
        destination_site_json = simplejson.dumps(destination_site_dict)
        user_info_json = simplejson.dumps(user_info)

        self.response.out.write(
            template.render('mlabns/templates/lookup_map.html', {
                'sites' : site_list_json,
                'user' : user_info_json,
                'destination' : destination_site_json }))
