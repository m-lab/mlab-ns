from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import taskqueue

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import resolver
from mlabns.util import util

import json
import logging
import time

class LookupHandler(webapp.RequestHandler):
    """Routes GET requests to the appropriate SliverTools."""

    def post(self):
        """Not implemented."""
        return util.send_not_found(self)

    def get(self):
        """Handles an HTTP GET request.

        The URL must be in the following format:
        'http://mlab-ns.appspot.com/tool-name?query_string',
        where tool-name is one of the tools running on M-Lab.
        For more information about the URL and the supported arguments
        in the query string, see the design doc at http://goo.gl/48S22.
        """
        query = resolver.LookupQuery()
        query.initialize_from_http_request(self.request)

        sliver_tool = resolver.Resolver(query).answer_query()

        if query.response_format == message.FORMAT_JSON:
            self.send_json_response(sliver_tool, query)
        elif query.response_format == message.FORMAT_HTML:
            self.send_html_response(sliver_tool, query)
        elif query.response_format == message.FORMAT_REDIRECT:
            self.send_redirect_response(sliver_tool, query)
        elif query.response_format == message.FORMAT_MAP:
            self.send_map_response(sliver_tool, query)
        else:
            # TODO (claudiu) Discuss what should be the default behaviour.
            # I think json it's OK since is valid for all tools, while
            # redirect only applies to web-based tools (e.g., npad)
            self.send_json_response(sliver_tool, query)

        # TODO (claudiu) Add a FORMAT_TYPE column in the BigQuery schema.
        self.log_request(query, sliver_tool)

    def send_json_response(self, sliver_tool, query):
        """Sends the response to the lookup request in json format.

        Args:
            sliver_tool: A SliverTool instance, representing the best sliver
                tool selected for this lookup request.
            query: A LookupQuery instance representing the user lookup request.

        """
        if sliver_tool is None:
            return util.send_not_found(self, 'json')
        data = {}
        ip = sliver_tool.sliver_ipv4
        fqdn = sliver_tool.fqdn_ipv4

        if query.address_family == message.ADDRESS_FAMILY_IPv6:
            ip = sliver_tool.sliver_ipv6
            fqdn = sliver_tool.fqdn_ipv6

        if sliver_tool.http_port:
            data['url'] = ':' . join ([
                'http://' + fqdn, sliver_tool.http_port])

        data['fqdn'] = fqdn
        data['ip'] = ip
        data['site'] = sliver_tool.site_id
        data['city'] = sliver_tool.city
        data['country'] = sliver_tool.country

        json_data = json.dumps(data)
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_data)

    def send_html_response(self, sliver_tool, query):
        """Sends the response to the lookup request in html format.

        Args:
            sliver_tool: A SliverTool instance, representing the best sliver
                tool selected for this lookup request.
            query: A LookupQuery instance representing the user lookup request.

        """
        if sliver_tool is None:
            return util.send_not_found(self, 'html')
        records = []
        records.append(sliver_tool)
        values = {'records' : records}
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.out.write(
            template.render(
                'mlabns/templates/lookup_response.html', values))

    def send_redirect_response(self, sliver_tool, query):
        """Sends an HTTP redirect (for web-based tools only).

        Args:
            sliver_tool: A SliverTool instance, representing the best sliver
                tool selected for this lookup request.
            query: A LookupQuery instance representing the user lookup request.

        """
        if sliver_tool is None:
            return util.send_not_found(self, 'html')
        if sliver_tool.http_port:
            url = '' .join([
                'http://', sliver_tool.fqdn_ipv4, ':', sliver_tool.http_port])
            return self.redirect(str(url))

        return util.send_not_found(self, 'html')

    def send_map_response(self, sliver_tool, query):
        """Displays the map with the user location and the destination site.

        Args:
            destination_sliver_tool: A SliverTool instance. Details about the
                sliver tool are displayed in an info window associated to the
                sliver_tool's site marker.
            lookup_query: A LookupQuery instance.
            site: A Site instance, used to draw a marker on the map.
        """
        if sliver_tool is None:
            return util.send_not_found(self, 'html')

        destination_site_dict = {}
        destination_site_dict['site_id'] = sliver_tool.site_id
        destination_site_dict['city'] = sliver_tool.city
        destination_site_dict['country'] = sliver_tool.country
        destination_site_dict['latitude'] = sliver_tool.latitude
        destination_site_dict['longitude'] = sliver_tool.longitude

        fqdn = sliver_tool.fqdn_ipv4
        if query.address_family == message.ADDRESS_FAMILY_IPv6:
            fqdn = sliver_tool.fqdn_ipv6

        destination_info = fqdn
        # For web-based tools set this to the URL.
        if sliver_tool.http_port:
            url = ''.join([
                'http://', fqdn, ':', sliver_tool.http_port])
            destination_info = ''.join([
                '<a class="footer" href=', url, '>', url, '</a>'])

        destination_site_dict['info'] = ''.join([
            '<div id=siteShortInfo>',
            '<h2>',
            sliver_tool.city, ', ', sliver_tool.country,
            '</h2>',
            destination_info,
            '</div>'])

        # Get the list af all other sites.
        candidates = resolver.Resolver(query).get_candidates()

        site_list = []
        for candidate in candidates:
            if candidate.site_id == sliver_tool.site_id:
                continue
            site_dict = {}
            site_dict['site_id'] = candidate.site_id
            site_dict['city'] = candidate.city
            site_dict['country'] = candidate.country
            site_dict['latitude'] = candidate.latitude
            site_dict['longitude'] = candidate.longitude
            site_list.append(site_dict)

        user_info = {}
        user_info['city'] = query.city
        user_info['country'] = query.country
        user_info['latitude'] = query.latitude
        user_info['longitude'] = query.longitude

        site_list_json = json.dumps(site_list)
        destination_site_json = json.dumps(destination_site_dict)
        user_info_json = json.dumps(user_info)

        self.response.out.write(
            template.render('mlabns/templates/lookup_map.html', {
                'sites' : site_list_json,
                'user' : user_info_json,
                'destination' : destination_site_json }))

    def log_request(self, query, sliver_tool):
        """Logs the request. Each entry in the log is uploaded to BigQuery.

        Args:
            query: A LookupQuery instance.
            sliver_tool: SliverTool entity chosen in the server
                selection phase.
        """
        if sliver_tool is None:
            # TODO(claudiu) Log also the error.
            return

        is_ipv6 = 'False'
        ip = sliver_tool.sliver_ipv4
        fqdn = sliver_tool.fqdn_ipv4
        if query.address_family == message.ADDRESS_FAMILY_IPv6:
            is_ipv6 = 'True'
            ip = sliver_tool.sliver_ipv6
            fqdn = sliver_tool.fqdn_ipv6

        # TODO(claudiu) This might change based on the privacy doc
        # (see http://goo.gl/KYPQW).
        logging.debug(
            '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s',
            '[lookup]',
            query.tool_id, query.policy, query.ip_address, is_ipv6,
            query.city, query.country, query.latitude, query.longitude,
            sliver_tool.slice_id, sliver_tool.server_id, ip, fqdn,
            sliver_tool.site_id, sliver_tool.city, sliver_tool.country,
            sliver_tool.latitude, sliver_tool.longitude, long(time.time()))
