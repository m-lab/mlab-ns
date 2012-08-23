from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import taskqueue

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
        if query.policy == message.POLICY_METRO:
            sliver_tool = resolver.MetroResolver().answer_query(query)
        elif query.policy == message.POLICY_GEO:
            sliver_tool = resolver.GeoResolver().answer_query(query)

        self.log_request(query, sliver_tool)

        if query.response_format == message.FORMAT_JSON:
            self.send_json_response(sliver_tool)
        elif query.response_format == message.FORMAT_HTML:
            self.send_html_response(sliver_tool)
        else:
            self.send_redirect_response(sliver_tool)

    def send_json_response(self, sliver_tool):
        if sliver_tool is None:
            return util.send_not_found(self)
        data = {}

        if sliver_tool.sliver_ipv4 != 'off':
            data['ipv4'] = sliver_tool.sliver_ipv4
        if sliver_tool.sliver_ipv6 != 'off':
            data['ipv6'] = sliver_tool.sliver_ipv6
        if sliver_tool.url != 'off':
            data['url'] = sliver_tool.url
        data['fqdn'] = sliver_tool.fqdn
        data['site'] = sliver_tool.site_id

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

        if sliver_tool.url == 'off':
            return self.send_json_response(sliver_tool)

        return self.redirect(str(sliver_tool.url))

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
            is_ipv6 = 'False'
            sliver_ip = sliver_tool.sliver_ipv4
            if query.ipv6_flag:
                is_ipv6 = 'True'
                sliver_ip = sliver_tool.sliver_ipv6

            logging.debug(
                '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s',
                '[lookup]',
                query.tool_id, query.policy, query.ip_address, is_ipv6,
                query.city, query.country, query.latitude, query.longitude,
                sliver_tool.slice_id, sliver_tool.server_id, sliver_ip,
                sliver_tool.fqdn, site.site_id, site.city, site.country,
                site.latitude, site.longitude, long(time.time()))

        #record = {}
        #record['tool_id'] = 'npad'
        #record['policy'] = 'geo'
        #record['user_ip'] = '92.20.246.113'
        #record['is_ipv6'] = 'false'
        #record['user_city'] = 'norwich'
        #record['user_country'] = 'GB'
        #record['user_latitude'] = '52.628101'
        #record['user_longitude'] = '1.299349'
        #record['slice_id'] = 'iupui_npad'
        #record['server_id'] = 'mlab3'
        #record['server_fqdn'] = 'npad.iupui.mlab3.lhr01.measurement-lab.org'
        #record['site_id'] = 'lhr01'
        #record['site_city'] = 'London'
        #record['site_country'] = 'UK'
        #record['site_latitude'] = '51.469722'
        #record['site_longitude'] = '-0.451389'
        #record['log_time'] = '1345317886'
        #record['latency'] = '0.507412'
        #record['user_agent'] = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.75 Safari/537.1'
        #taskqueue.add(url='/bigquery', params=record)
