from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.util import distance
from mlabns.db import model
from mlabns.util import message
from mlabns.util import resolver

import logging
import time

class LookupHandler(webapp.RequestHandler):
    """Routes GET requests to the appropriate SliverTools."""

    def post(self):
        """Not implemented."""
        return self.not_found()

    def get(self):
        """Handles an HTTP GET request."""

        query = message.LookupQuery(self.request)
        sliver_tool = None
        if query.metro:
            metro_resolver = resolver.MetroResolver()
            sliver_tool = metro_resolver.answer_query(query)
        elif query.policy_geo():
            geo_resolver = resolver.GeoResolver()
            sliver_tool = geo_resolver.answer_query(query)

        if sliver_tool is None:
            logging.error('No results found for %s.', self.request.path)
            # TODO(claudiu) Use a default url if something goes wrong.
            return self.not_found()

        # TODO(claudiu) Remove this, is only for debugging.
        # self.redirect(sliver_tool.url)

        self.log_request(query, sliver_tool)

        records = []
        records.append(sliver_tool)
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/sliver_tool.html', values))

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
                '[LOOKUP] \
                Tool Id:%s \
                Policy:%s \
                User IP:%s \
                User City:%s \
                User Country:%s \
                User Lat/Long:%s \
                Slice Id:%s \
                Server Id:%s \
                Site Id:%s \
                Site City:%s \
                Site Country:%s \
                Site Lat/Long:%s',
                query.tool_id,
                query.policy,
                query.user_ip,
                query.user_city,
                query.user_country,
                query.user_lat_long,
                sliver_tool.slice_id,
                sliver_tool.server_id,
                site.site_id,
                site.city,
                site.country,
                site.lat_long)

            # Log the request to db.
            # TOD(claudiu) Add a counter for IPv4 and IPv6.
            lookup_entry = model.Lookup(
                tool_id=query.tool_id,
                policy=query.policy,
                user_ip=query.user_ip,
                user_city=query.user_city,
                user_country=query.user_country,
                user_lat_long=query.user_lat_long,
                slice_id=sliver_tool.slice_id,
                server_id=sliver_tool.server_id,
                site_id=site.site_id,
                site_city=site.city,
                site_country=site.country,
                site_lat_long=site.lat_long,
                key_name=query.user_ip)
            lookup_entry.put()
