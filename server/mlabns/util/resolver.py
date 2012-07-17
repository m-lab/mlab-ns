from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import distance
from mlabns.util import message

import logging
import random
import time


class LookupQuery:
    def __init__(self, request):
        self.tool_id = ''
        self.policy = ''
        self.response_type = ''
        self.metro = ''
        self.user_ip = ''
        self.user_city = ''
        self.user_country = ''
        self.user_lat_long = ''

        parts = request.path.strip('/').split('/')
        self.tool_id = parts[0]
        self.user_ip = request.remote_addr
        self.policy = request.get(message.POLICY)
        self.metro = request.get(message.METRO)
        self.response_type = request.get(message.RESPONSE_TYPE)

        # Default to geo policy.
        if not self.policy:
            self.policy = message.POLICY_GEO

        if message.HEADER_CITY in request.headers:
            self.user_city = request.headers[message.HEADER_CITY]
        if message.HEADER_COUNTRY in request.headers:
            self.user_country = request.headers[message.HEADER_COUNTRY]
        if message.HEADER_LAT_LONG in request.headers:
            self.user_lat_long = request.headers[message.HEADER_LAT_LONG]

        logging.info('Policy is "%s".', self.policy)

    def is_policy_geo(self):
        return self.policy == message.POLICY_GEO

    def is_policy_rtt(self):
        return False

    def is_format_json(self):
        return (self.response_type == message.FORMAT_JSON)

    def is_format_protobuf(self):
        return (self.response_type == message.FORMAT_PROTOBUF)

class GeoResolver:
    """Implements the closest-node policy."""

    def get_sliver_tool_candidates(self, lookup_query):
        """Find candidates for server selection.

        Select all the sliver tools that match the requirements
        for the policy specified in the request.Currently only
        the 'geo' policy is implemented, so all the sliver tools
        available that match the 'tool_id' will be selected.
        Looks only for SliverTool entities that are online, and who
        recently updated their status.

        Return:
            A list of SliverTool entities.
        """

        oldest_timestamp = long(time.time()) - constants.UPDATE_INTERVAL
        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status = 'online' "
            "AND timestamp > :timestamp ",
            tool_id=lookup_query.tool_id,
            timestamp=oldest_timestamp)
            # TODO (claudiu) Check ipv6/ipv4.
        return candidates.fetch(constants.MAX_FETCHED_RESULTS)

    def answer_query(self, query):
        """Select the geographically closest sliver tool.

        Args:
            sliver_tools: A list of SliverTool entities that match the
                requirements of the request.

        Return:
            A SliverTool entity that best matches the request.
        """
        sliver_tools = self.get_sliver_tool_candidates(query)

        logging.info('Found %s results.', len(sliver_tools))
        if not sliver_tools:
            logging.error('No results found for %s.', query.tool_id)
            return None

        if not query.user_lat_long:
            logging.error('No results found for %s.', query.tool_id)
            return sliver_tools[0]

        min_distance = float('+inf')
        nodes = []
        distances = {}

        # Compute for each sliver_tool the distance and update the
        # best match if the distance is less that the current minimum.
        # To avoid computing the distances twice, cache the results in
        # a dict.
        for sliver_tool in sliver_tools:
            # Check if we already computed this distance.
            if (distances.has_key(sliver_tool.lat_long)):
                current_distance = distances[sliver_tool.lat_long]
            else:
                # Compute the distance.
                current_distance = distance.distance(
                    query.user_lat_long,
                    sliver_tool.lat_long)

                # Add the distance to the dict.
                distances[sliver_tool.lat_long] = current_distance

            if (current_distance <= min_distance):
                min_distance = current_distance
                nodes.insert(0, sliver_tool)

        closest_nodes = []
        for node in nodes:
            if distances[node.lat_long] <= min_distance * constants.EPSILON:
                closest_nodes.append(node)
            else:
                break

        return random.choice(closest_nodes)

class MetroResolver:
    """Implements the metro policy."""

    def answer_query(self, query):
        """Select the sliver tool that best matches the requirements.

        Select all the sliver tools that match the 'metro' requirements
        specified in the request, order the results by timestamp and
        return the first result.

        Return:
            A SliverTool entity if available, or None.
        """

        sites = model.Site.all().filter("metro =", query.metro).fetch(
            constants.MAX_FETCHED_RESULTS)

        logging.info('No result found for metro %s.', len(sites))
        if len(sites) == 0:
            logging.info('No result found for metro %s.', query.metro)
            return None

        site_id_list = []
        for site in sites:
            site_id_list.append(site.site_id)

        oldest_timestamp = long(time.time()) - constants.UPDATE_INTERVAL
        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status = 'online' "
            "AND timestamp > :timestamp "
            "AND site_id in :site_id_list ",
            tool_id=query.tool_id,
            timestamp=oldest_timestamp,
            site_id_list=site_id_list).fetch(constants.MAX_FETCHED_RESULTS)
            # TODO (claudiu) Check ipv6/ipv4.

        if not candidates:
            return None

        return random.choice(candidates)
