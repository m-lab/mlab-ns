import json
import logging
import time

from mlabns.db import model
from mlabns.util import fqdn_rewrite
from mlabns.util import lookup_query
from mlabns.util import message
from mlabns.util import resolver
from mlabns.util import util

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


def _create_tool_url(fqdn, http_port):
    """Create an HTTP URL for a tool.

    Args:
        fqdn: A tool FQDN (already processed by fqdn_rewrite).
        http_port: The HTTP port number part of the URL.

    Returns:
        A constructed tool HTTP URL with protocol and http port.
    """
    return 'http://%s:%s' % (fqdn, http_port)


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
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.request)

        logging.info('Policy is %s', query.policy)
        lookup_resolver = resolver.new_resolver(query.policy)
        sliver_tools = lookup_resolver.answer_query(query)

        if sliver_tools is None:
            return util.send_not_found(self, query.response_format)

        if query.response_format == message.FORMAT_JSON:
            self.send_json_response(sliver_tools, query)
        elif query.response_format == message.FORMAT_HTML:
            self.send_html_response(sliver_tools, query)
        elif query.response_format == message.FORMAT_REDIRECT:
            self.send_redirect_response(sliver_tools, query)
        elif query.response_format == message.FORMAT_BT:
            self.send_bt_response(sliver_tools, query)
        elif query.response_format == message.FORMAT_MAP:
            candidates = lookup_resolver.get_candidates(query)
            self.send_map_response(sliver_tools, query, candidates)
        else:
            # TODO (claudiu) Discuss what should be the default behaviour.
            # I think json it's OK since is valid for all tools, while
            # redirect only applies to web-based tools (e.g., npad)
            self.send_json_response(sliver_tools, query)

        # TODO (claudiu) Add a FORMAT_TYPE column in the BigQuery schema.
        self.log_request(query, sliver_tools)

    def send_bt_response(self, sliver_tools, query):
        """Sends the response to the lookup request in bt format.

        Args:
            sliver_tools: A list of SliverTool instances,
                representing the best sliver
                tools selected for this lookup request.
            query: A LookupQuery instance representing the user lookup request.
        """
        if type(sliver_tools) is not list:
            logging.error("Problem: sliver_tools is not a list.")
            return

        bt_data = ""
        for sliver_tool in sliver_tools:
            fqdn = fqdn_rewrite.rewrite(sliver_tool.fqdn,
                                        query.tool_address_family,
                                        sliver_tool.tool_id)

            data = sliver_tool.city
            data += ", "
            data += sliver_tool.country

            data += "|"
            data += fqdn
            data += "\n"

            bt_data += data
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(bt_data)

    def send_json_response(self, sliver_tools, query):
        """Sends the response to the lookup request in json format.

        Args:
            sliver_tools: A list of SliverTool instances,
                representing the best sliver
                tool selected for this lookup request.
            query: A LookupQuery instance representing the user lookup request.
        """
        array_response = False
        if len(sliver_tools) > 1:
            array_response = True

        if type(sliver_tools) is not list:
            logging.error("Problem: sliver_tools is not a list.")
            return

        tool = None
        json_data = ""
        for sliver_tool in sliver_tools:
            data = {}

            if tool == None:
                tool = model.get_tool_from_tool_id(sliver_tool.tool_id)

            if query.tool_address_family == message.ADDRESS_FAMILY_IPv4:
                ips = [sliver_tool.sliver_ipv4]
            elif query.tool_address_family == message.ADDRESS_FAMILY_IPv6:
                ips = [sliver_tool.sliver_ipv6]
            else:
                ips = []
                if sliver_tool.status_ipv4 == message.STATUS_ONLINE:
                    ips.append(sliver_tool.sliver_ipv4)
                if sliver_tool.status_ipv6 == message.STATUS_ONLINE:
                    ips.append(sliver_tool.sliver_ipv6)

            fqdn = fqdn_rewrite.rewrite(sliver_tool.fqdn,
                                        query.tool_address_family,
                                        sliver_tool.tool_id)
            if sliver_tool.http_port:
                data['url'] = _create_tool_url(fqdn, sliver_tool.http_port)
            if sliver_tool.server_port:
                data['port'] = sliver_tool.server_port

            data['fqdn'] = fqdn
            data['ip'] = ips
            data['site'] = sliver_tool.site_id
            data['city'] = sliver_tool.city
            data['country'] = sliver_tool.country

            if sliver_tool.tool_extra and tool.show_tool_extra:
                data['tool_extra'] = sliver_tool.tool_extra

            if json_data != "":
                json_data += ","
            json_data += json.dumps(data)

        if array_response:
            json_data = "[" + json_data + "]"
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_data)

    def send_html_response(self, sliver_tools, query):
        """Sends the response to the lookup request in html format.

        Args:
            sliver_tools: A list of SliverTool instances, representing the best
                sliver tool selected for this lookup request.
            query: A LookupQuery instance representing the user lookup request.
        """
        if type(sliver_tools) != list:
            logging.error("Problem: sliver_tools is not a list.")
            return

        records = []
        records.extend(sliver_tools)
        values = {'records': records}
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.out.write(template.render(
            'mlabns/templates/lookup_response.html', values))

    def send_redirect_response(self, sliver_tools, query):
        """Sends an HTTP redirect (for web-based tools only).

        Args:
            sliver_tools: A list of SliverTool instances, representing the best
                sliver tool selected for this lookup request.
            query: A LookupQuery instance representing the user lookup request.
        """
        if type(sliver_tools) != list:
            logging.error("Problem: sliver_tools is not a list.")
            return

        sliver_tool = sliver_tools[0]

        if sliver_tool.http_port:
            fqdn = fqdn_rewrite.rewrite(sliver_tool.fqdn,
                                        query.tool_address_family,
                                        sliver_tool.tool_id)
            url = _create_tool_url(fqdn, sliver_tool.http_port)
            return self.redirect(url)

        return util.send_not_found(self, 'html')

    def send_map_response(self, sliver_tool, query, candidates):
        """Shows the result of the query in a map.

        The map displays a set of markers representing the user location,
        all the available sites and a line connecting the user to the
        destination site.

        Args:
            sliver_tool: A SliverTool instance. Details about the
                sliver tool are displayed in an info window associated to the
                sliver_tool's site marker.
            query: A LookupQuery instance.
            candidates: A list of SliverTool entities that match the
                 requirements specified in 'query'.
        """
        destination_site_dict = {}
        destination_site_dict['site_id'] = sliver_tool.site_id
        destination_site_dict['city'] = sliver_tool.city
        destination_site_dict['country'] = sliver_tool.country
        destination_site_dict['latitude'] = sliver_tool.latitude
        destination_site_dict['longitude'] = sliver_tool.longitude

        fqdn = fqdn_rewrite.rewrite(sliver_tool.fqdn, query.tool_address_family,
                                    sliver_tool.tool_id)

        # For web-based tools set this to the URL.
        if sliver_tool.http_port:

            url = _create_tool_url(fqdn, sliver_tool.http_port)
            destination_info = (
                '<a class="footer" href=' + url + '>' + url + '</a>')
        else:
            destination_info = fqdn

        destination_site_dict['info'] = \
            '<div id=siteShortInfo><h2>%s, %s</h2>%s</div>' % \
            (sliver_tool.city, sliver_tool.country, destination_info)

        candidate_site_list = []
        for candidate in candidates:
            if candidate.site_id == sliver_tool.site_id:
                continue
            candidate_site_dict = {}
            candidate_site_dict['site_id'] = candidate.site_id
            candidate_site_dict['city'] = candidate.city
            candidate_site_dict['country'] = candidate.country
            candidate_site_dict['latitude'] = candidate.latitude
            candidate_site_dict['longitude'] = candidate.longitude
            candidate_site_list.append(candidate_site_dict)

        user_info = {}
        user_info['city'] = query.city
        user_info['country'] = query.country
        user_info['latitude'] = query.latitude
        user_info['longitude'] = query.longitude

        candidate_site_list_json = json.dumps(candidate_site_list)
        destination_site_json = json.dumps(destination_site_dict)
        user_info_json = json.dumps(user_info)

        self.response.out.write(template.render(
            'mlabns/templates/lookup_map.html', {
                'sites': candidate_site_list_json,
                'user': user_info_json,
                'destination': destination_site_json
            }))

    def log_request(self, query, sliver_tools):
        """Logs the request. Each entry in the log is uploaded to BigQuery.

        Args:
            query: A LookupQuery instance.
            sliver_tools: SliverTool entity chosen in the server selection
                phase.
        """
        if sliver_tools is None:
            # TODO(claudiu) Log also the error.
            return
        if type(sliver_tools) != list:
            logging.error("Problem: sliver_tools is not a list.")
            return

        user_agent = ''
        if 'User-Agent' in self.request.headers:
            user_agent = self.request.headers['User-Agent']

        sliver_tool_info = ""
        for sliver_tool in sliver_tools:
            fqdn = fqdn_rewrite.rewrite(sliver_tool.fqdn,
                                        query.tool_address_family,
                                        sliver_tool.tool_id)
            sliver_tool_info += "(%s %s %s %s %s %s %s %s %s %s %s) " % \
                (sliver_tool.slice_id,
                sliver_tool.server_id,
                sliver_tool.sliver_ipv4,
                sliver_tool.sliver_ipv6,
                sliver_tool.fqdn,
                fqdn,
                sliver_tool.site_id,
                sliver_tool.city,
                sliver_tool.country,
                sliver_tool.latitude,
                sliver_tool.longitude)

        # See the privacy doc at http://mlab-ns.appspot.com/privacy.
        # The list of these fields is consistent with the BigQuery schema,
        # except for the request latency field, that is added in the log2bq.py
        # since it's automatically computed by GAE for every request and
        # included in the request_log object.
        logging.info('[lookup]'
                     '%s,%s,%s,'
                     '%s,'
                     '%s,%s,%s,%s,%s,%s,%s',
                     # Info about the user:
                     query.tool_address_family,
                     query.ip_address,
                     user_agent,
                     sliver_tool_info,
                     # Info about the request:
                     query.tool_id,
                     query.policy,
                     query.response_format,
                     query._geolocation_type,
                     query.metro,
                     str(time.time()),
                     # Calculated information about the lookup:
                     str(query.distance))
