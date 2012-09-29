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

        sliver_tool = None
        if query.policy == message.POLICY_METRO:
            sliver_tool = resolver.MetroResolver().answer_query(query)
        elif query.policy == message.POLICY_GEO:
            sliver_tool = resolver.GeoResolver().answer_query(query)
        elif query.policy == message.POLICY_RANDOM:
            sliver_tool = resolver.RandomResolver().answer_query(query)

        self.log_request(query, sliver_tool)

        if query.response_format == message.FORMAT_JSON:
            self.send_json_response(sliver_tool, query)
        elif query.response_format == message.FORMAT_HTML:
            self.send_html_response(sliver_tool, query)
        else:
            self.send_redirect_response(sliver_tool, query)

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

        if sliver_tool.http_port != 'off':
            data['url'] = ':' . join ([
                'http://'+fqdn, sliver_tool.http_port])

        data['fqdn'] = fqdn
        data['ip'] = ip
        data['site'] = sliver_tool.site_id

        sites = memcache.get('sites')
        if sites is None:
            sites = {}
            entities = model.Site.gql('ORDER by site_id DESC').fetch(
                constants.MAX_FETCHED_RESULTS)
            for entity in entities:
                sites[entity.site_id] = entity
            memcache.set('sites', sites)

        site = sites[sliver_tool.site_id]
        data['city'] = site.city
        data['country'] = site.country
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
        if sliver_tool.http_port != 'off':
            url = '' .join([
                'http://', sliver_tool.fqdn_ipv4, ':', sliver_tool.http_port])
            return self.redirect(str(url))

        return self.send_json_response(sliver_tool, query)

    def log_request(self, query, sliver_tool):
        """Logs the request. Each entry in the log is uploaded to BigQuery.

        Args:
            query: A LookupQuery instance.
            sliver_tool: SliverTool entity chosen in the server
                selection phase.
        """
        sites = memcache.get('sites')
        if sites is None:
            sites = {}
            entities = model.Site.gql('ORDER by site_id DESC').fetch(
                constants.MAX_FETCHED_RESULTS)
            for entity in entities:
                sites[entity.site_id] = entity
            memcache.set('sites', sites)

        if sliver_tool is None or not sliver_tool.site_id in sites:
            # TODO(claudiu) Log also the error.
            return

        site = sites[sliver_tool.site_id]
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
            sliver_tool.slice_id, sliver_tool.server_id, ip,
            fqdn, site.site_id, site.city, site.country,
            site.latitude, site.longitude, long(time.time()))
