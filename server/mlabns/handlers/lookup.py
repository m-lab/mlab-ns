from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

from mlabns.db import model
from mlabns.util import distance
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
        """Handles an HTTP GET request."""

        query = resolver.LookupQuery()
        query.initialize_from_http_request(self.request)
        sliver_tool = None
        if query.metro:
            sliver_tool = resolver.MetroResolver().answer_query(query)
        elif query.policy == message.POLICY_GEO:
            sliver_tool = resolver.GeoResolver().answer_query(query)

        logging.info('Format: %s', query.response_format)
        self.log_request(query, sliver_tool)

        if query.response_format == message.FORMAT_JSON:
            self.send_json_response(sliver_tool)
        elif query.response_format == message.FORMAT_PROTOBUF:
            self.send_protobuf_response(sliver_tool)
        elif query.response_format == message.FORMAT_HTML:
            self.send_html_response(sliver_tool)
        else:
            self.send_redirect_response(sliver_tool)

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
        json_data = json.dumps(data)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_data)

    def send_protobuf_response(self, sliver_tool):
        pass

    def send_html_response(self, sliver_tool):
        if sliver_tool is None:
            return util.send_not_found(self, 'html')
        records = []
        records.append(sliver_tool)
        values = {'records' : records}
        self.response.out.write(
            template.render(
                'mlabns/templates/lookup_response.html', values))

    def send_redirect_response(self, sliver_tool):
        if sliver_tool is None:
            return util.send_not_found(self, 'html')
        self.redirect(str(sliver_tool.url))

    def log_request(self,  query, sliver_tool):
        """Logs the request.

        Args:
            query: A LookupQuery instance.
            sliver_tool: SliverTool entity chosen in the server
                selection phase.
        """
        if sliver_tool is None:
            return

        site = model.Site.get_by_key_name(sliver_tool.site_id)

        if site is not None:
            # Log the request to file.
            logging.info(
                '[LOOKUP] Tool Id:%s Policy:%s \
                User IP:%s User City:%s User Country:%s \
                User Latitude: %s User Longitude: %s \
                Slice Id:%s Server Id:%s Site Id:%s \
                Site City:%s Site Country:%s \
                Site Latitude: %s Site Longitude: %s',
                query.tool_id, query.policy,
                query.ip_address, query.city, query.country,
                query.latitude, query.longitude,
                sliver_tool.slice_id, sliver_tool.server_id,site.site_id,
                site.city, site.country,
                site.latitude, site.longitude)

            # Log the request to db.
            # TODO(claudiu) Add a counter for IPv4 and IPv6.
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
