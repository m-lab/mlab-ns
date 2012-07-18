from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.db import model
from mlabns.util import distance
from mlabns.util import resolver

import json
import logging
import time

class LookupHandler(webapp.RequestHandler):
    """Routes GET requests to the appropriate SliverTools."""

    def post(self):
        """Not implemented."""
        return self.not_found()

    def get(self):
        """Handles an HTTP GET request."""

        query = resolver.LookupQuery(self.request)
        sliver_tool = None
        if query.metro:
            sliver_tool = resolver.MetroResolver().answer_query(query)
        elif query.is_policy_geo():
            sliver_tool = resolver.GeoResolver().answer_query(query)

        if query.is_format_json():
            return self.send_json(sliver_tool)

        if query.is_format_protobuf():
            return self.send_protobuf(sliver_tool)

        if sliver_tool is None:
            logging.error('No results found for %s.', self.request.path)
            # TODO(claudiu) Use a default url if something goes wrong.
            return self.not_found()

        # TODO(claudiu) Remove this comment.
        # Default to HTTP redirect.
        # self.redirect(sliver_tool.url)

        # TODO(claudiu) Remove this, is only for debugging.
        self.log_request(query, sliver_tool)

        records = []
        records.append(sliver_tool)
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/sliver_tool.html', values))

    def send_json(self, sliver_tool):
        data = {}
        if sliver_tool is not None:
            data['slice_id'] = sliver_tool.slice_id
            data['server_id'] = sliver_tool.server_id
            data['site'] = sliver_tool.site_id
            data['sliver_ipv4'] = sliver_tool.sliver_ipv4
            data['sliver_ipv6'] = sliver_tool.sliver_ipv6
            data['url'] = sliver_tool.url
        json_data = json.dumps(data)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_data)

    def send_protobuf(self, sliver_tool):
        pass

    def not_found(self):
        self.error(404)
        self.response.out.write(
            template.render('mlabns/templates/not_found.html', {}))

    def send_not_found(self):
        self.error(404)
        self.response.out.write(
            template.render('mlabns/templates/not_found.html', {}))

    def log_request(self,  query, sliver_tool):
        """Logs the request.

        Args:
            query: A LookupQuery instance.
            sliver_tool: SliverTool entity chosen in the server
                selection phase.
        """
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
                query.user_ip, query.user_city, query.user_country,
                query.latitude, query.longitude,
                sliver_tool.slice_id, sliver_tool.server_id,site.site_id,
                site.city, site.country,
                site.latitude, site.longitude)

            # Log the request to db.
            # TOD(claudiu) Add a counter for IPv4 and IPv6.
            lookup_entry = model.Lookup(
                tool_id=query.tool_id,
                policy=query.policy,
                user_ip=query.user_ip,
                user_city=query.user_city,
                user_country=query.user_country,
                user_latitude=query.latitude,
                user_longitude=query.longitude,
                slice_id=sliver_tool.slice_id,
                server_id=sliver_tool.server_id,
                site_id=site.site_id,
                site_city=site.city,
                site_country=site.country,
                site_latitude=site.latitude,
                site_longitude=site.longitude)
                #key_name=query.user_ip)
            lookup_entry.put()
