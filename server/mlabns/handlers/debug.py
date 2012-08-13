from google.appengine.api import memcache
from django.utils import simplejson

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.db import model
from mlabns.util import constants
from mlabns.util  import util
from mlabns.util import message
from mlabns.util import resolver
from mlabns.util.geo import maxmind

import logging
import time

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
        lookup_query.initialize_from_http_request(self.request)
        if (parts[0] == 'geo'):
            ip_address = self.request.get(message.REMOTE_ADDRESS);
            geo_record = maxmind.get_ip_geolocation(ip_address);
            lookup_query.city = geo_record.city
            lookup_query.country = geo_record.country
            lookup_query.latitude = geo_record.latitude
            lookup_query.longitude = geo_record.longitude
            lookup_query.ip_address = ip_address

        lookup_query.tool_id = parts[1]

        sliver_tool = None
        if lookup_query.metro:
            metro_resolver = resolver.MetroResolver()
            sliver_tool = metro_resolver.answer_query(lookup_query)
        elif lookup_query.policy_geo:
            geo_resolver = resolver.GeoResolver()
            sliver_tool = geo_resolver.answer_query(lookup_query)

        if sliver_tool is None:
            logging.error('No results found for %s.', self.request.path)
            # TODO(claudiu) Use a default url if something goes wrong.
            return util.send_not_found(self)

        if lookup_query.response_format == message.FORMAT_JSON:
            return self.send_json_response(sliver_tool)

        # TODO(claudiu) Move this in util.py.
        self.log_request(lookup_query, sliver_tool)

        if lookup_query.latitude == 0.0:
            lookup_query.city = "Rome"
            lookup_query.country = "Italy"
            lookup_query.latitude = 41.9000
            lookup_query.longitude = 12.500

        if lookup_query.latitude != 0.0:
            return self.send_map_view(sliver_tool, lookup_query)

        return self.send_html_view(sliver_tool)

    def get_site_list(self, lookup_query):
        sliver_tools = self.get_sliver_tool_candidates(lookup_query)
        sites = []
        for sliver_tool in sliver_tools:
            site = model.Site.get_by_key_name(sliver_tool.site_id)
            sites.append(site)
        return sites

    def get_sliver_tool_candidates(self, lookup_query):
        """Find candidates for server selection.

        Args:
            lookup_query: A LookupQuery instance.

        Returns:
            A list of SliverTool entities that match the requirements
            specified in the 'lookup_query'.
        """

        oldest_timestamp = long(time.time()) - constants.UPDATE_INTERVAL

        # First try to get the sliver tools from the cache.
        sliver_tools = memcache.get(lookup_query.tool_id)
        if sliver_tools is not None:
            logging.debug('Sliver tools found in memcache')
            candidates = []
            for sliver_tool in sliver_tools.values():
                if (sliver_tool.update_request_timestamp > oldest_timestamp
                    and sliver_tool.status == message.STATUS_ONLINE):
                    candidates.append(sliver_tool)
            return candidates

        logging.debug('Sliver tools not found in cache, querying the db')
        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status = :status "
            "AND update_request_timestamp > :timestamp ",
            tool_id=lookup_query.tool_id,
            status=message.STATUS_ONLINE,
            timestamp=oldest_timestamp)
            # TODO (claudiu) Check ipv6/ipv4.
        return candidates.fetch(constants.MAX_FETCHED_RESULTS)

    def send_map_view(self, sliver_tool, lookup_query):

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
        destination_site['url'] = sliver_tool.url
        url_info = '';
        logging.info('URL: %s', sliver_tool.url)
        if sliver_tool.url != 'off':
            url_info = ''.join([
                '<a class="footer" href=',sliver_tool.url,'>',
                sliver_tool.url,'</a>'])

        logging.info('URL: %s', url_info)
        destination_site['info'] = ''.join([
            '<div id=siteShortInfo>',
            '<h2>',
            site.city, ',', site.country,
            '</h2>',
            url_info,
            '</div>'])

        # Get the list af all other sites.
        sites = self.get_site_list(lookup_query)
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
            template.render(
                'mlabns/templates/lookup_map.html',
                {
                    'sites' : site_list_json,
                    'user' : user_info_json,
                    'destination' : destination_site_json
                }))

    def send_html_view(self, sliver_tool):
        records = [sliver_tool]
        self.response.out.write(
            template.render(
                'mlabns/templates/info.html', {'records' : records}))

    def log_request(self,  query, sliver_tool):
        """Logs the request.

        Args:
            query: A LookupQuery instance.
            sliver_tool: SliverTool entity chosen in the server
                selection phase.
        """
        # TODO(claudiu) This should be for diagnostic only, so
        # the logs sould be kept just a couple of days.

        site = model.Site.get_by_key_name(sliver_tool.site_id)

        if site is not None:
            # Log the request to file.
            # Log the request to db.
            # TOD(claudiu) Add a counter for IPv4 and IPv6.
            lookup_entry = model.Lookup(
                tool_id=query.tool_id,
                policy=query.policy,
                user_ip=query.ip_address,
                user_city=query.city,
                user_country=query.country,
                user_latitude=query.latitude,
                user_longitude=query.longitude,
                slice_id=sliver_tool.slice_id,
                server_id=sliver_tool.server_id,
                site_id=site.site_id,
                site_city=site.city,
                site_country=site.country,
                site_latitude=site.latitude,
                site_longitude=site.longitude,
                key_name=query.ip_address)
            lookup_entry.put()

    def send_json_response(self, sliver_tool):
        if sliver_tool is None:
            return util.send_not_found(self)
        data = {}
        data['slice_id'] = sliver_tool.slice_id
        data['server_id'] = sliver_tool.server_id
        data['site_id'] = sliver_tool.site_id
        data['sliver_ipv4'] = sliver_tool.sliver_ipv4
        data['sliver_ipv6'] = sliver_tool.sliver_ipv6
        data['url'] = sliver_tool.url
        json_data = simplejson.dumps(data)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_data)

class QueryHandler(webapp.RequestHandler):
    """Returns info of the server this client would be redirected to."""

    def post(self):
        """Not implemented."""
        return util.send_not_found(self)

    def get(self):
        """Handles an HTTP GET request."""

        query_type = self.request.path.split('/query/')[1]
        if query_type == 'server':
            return self.send_site_info()
        return self.send_lookup_info(query_type)

    def send_lookup_info(self, tool_id):
        """Returns the best SliverTool."""

        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument)

        lookup_query = resolver.LookupQuery()
        lookup_query.initialize_from_dictionary(dictionary)
        lookup_query.tool_id = tool_id

        sliver_tool = None
        if lookup_query.metro:
            metro_resolver = resolver.MetroResolver()
            sliver_tool = metro_resolver.answer_query(lookup_query)
        elif lookup_query.policy_geo:
            geo_resolver = resolver.GeoResolver()
            sliver_tool = geo_resolver.answer_query(lookup_query)

        if sliver_tool is None:
            logging.error('No results found for %s.', self.request.path)
            # TODO(claudiu) Use a default url if something goes wrong.
            return util.send_not_found(self)

        if lookup_query.response_format == message.FORMAT_JSON:
            return self.send_json_response(sliver_tool)

        # TODO(claudiu) Move this in util.py.
        self.log_request(lookup_query, sliver_tool)

        if lookup_query.latitude == 0.0:
            lookup_query.city = "Rome"
            lookup_query.country = "Italy"
            lookup_query.latitude = 41.9000
            lookup_query.longitude = 12.500

        if lookup_query.latitude != 0.0:
            return self.send_map_view(sliver_tool, lookup_query)

        return self.send_html_view(sliver_tool)

    def send_map_view(self, sliver_tool, lookup_query):

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
        destination_site['url'] = sliver_tool.url
        destination_site['info'] = '<div id=siteShortInfo>' + \
            '<h2>' + site.city + "," + site.country + '</h2>' + \
            '<a class="footer" href=' + sliver_tool.url + '>' + \
            sliver_tool.url + '</a></div>';

        # Get the list af all other sites.
        sites = model.Site.gql('ORDER BY site_id DESC')
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
            template.render(
                'mlabns/templates/lookup_map.html',
                {
                    'sites' : site_list_json,
                    'user' : user_info_json,
                    'destination' : destination_site_json
                }))

    def send_html_view(self, sliver_tool):
        records = [sliver_tool]
        self.response.out.write(
            template.render(
                'mlabns/templates/info.html', {'records' : records}))

    def send_json_response(self, sliver_tool):
        if sliver_tool is None:
            return util.send_not_found(self)
        data = {}
        data['slice_id'] = sliver_tool.slice_id
        data['server_id'] = sliver_tool.server_id
        data['site_id'] = sliver_tool.site_id
        data['sliver_ipv4'] = sliver_tool.sliver_ipv4
        data['sliver_ipv6'] = sliver_tool.sliver_ipv6
        data['url'] = sliver_tool.url
        json_data = simplejson.dumps(data)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_data)

class StatusHandler(webapp.RequestHandler):
    """Returns info of the server this client would be redirected to."""

    def post(self):
        """Not implemented."""
        return util.send_not_found(self)

    def get(self):
        """Handles an HTTP GET request."""

        query_type = self.request.path.split('/query/')[1]
        if query_type == 'server':
            return self.send_site_info()
        return self.send_lookup_info(query_type)

    def send_lookup_info(self, tool_id):
        """Returns the best SliverTool."""

        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument)

        lookup_query = resolver.LookupQuery()
        lookup_query.initialize_from_dictionary(dictionary)
        lookup_query.tool_id = tool_id

        sliver_tool = None
        if lookup_query.metro:
            metro_resolver = resolver.MetroResolver()
            sliver_tool = metro_resolver.answer_query(lookup_query)
        elif lookup_query.policy_geo:
            geo_resolver = resolver.GeoResolver()
            sliver_tool = geo_resolver.answer_query(lookup_query)

        if sliver_tool is None:
            logging.error('No results found for %s.', self.request.path)
            # TODO(claudiu) Use a default url if something goes wrong.
            return util.send_not_found(self)

        if lookup_query.response_format == message.FORMAT_JSON:
            return self.send_json_response(sliver_tool)

        # TODO(claudiu) Move this in util.py.
        self.log_request(lookup_query, sliver_tool)

        if lookup_query.latitude == 0.0:
            lookup_query.city = "Rome"
            lookup_query.country = "Italy"
            lookup_query.latitude = 41.9000
            lookup_query.longitude = 12.500

        if lookup_query.latitude != 0.0:
            return self.send_map_view(sliver_tool, lookup_query)

        return self.send_html_view(sliver_tool)

    def send_map_view(self, sliver_tool, lookup_query):

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
        destination_site['url'] = sliver_tool.url
        destination_site['info'] = '<div id=siteShortInfo>' + \
            '<h2>' + site.city + "," + site.country + '</h2>' + \
            '<a class="footer" href=' + sliver_tool.url + '>' + \
            sliver_tool.url + '</a></div>';

        # Get the list af all other sites.
        sites = model.Site.gql('ORDER BY site_id DESC')
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
            template.render(
                'mlabns/templates/lookup_map.html',
                {
                    'sites' : site_list_json,
                    'user' : user_info_json,
                    'destination' : destination_site_json
                }))

    def send_html_view(self, sliver_tool):
        records = [sliver_tool]
        self.response.out.write(
            template.render(
                'mlabns/templates/info.html', {'records' : records}))

    def send_json_response(self, sliver_tool):
        if sliver_tool is None:
            return util.send_not_found(self)
        data = {}
        data['slice_id'] = sliver_tool.slice_id
        data['server_id'] = sliver_tool.server_id
        data['site_id'] = sliver_tool.site_id
        data['sliver_ipv4'] = sliver_tool.sliver_ipv4
        data['sliver_ipv6'] = sliver_tool.sliver_ipv6
        data['url'] = sliver_tool.url
        json_data = simplejson.dumps(data)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_data)



