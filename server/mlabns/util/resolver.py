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
    def __init__(self):
        self.tool_id = None
        self.policy = None
        self.response_type = None
        self.metro = None
        self.user_ip = None
        self.user_city = None
        self.user_country = None
        self.latitude = 0.0
        self.longitude = 0.0

    def initalize_from_webapp_request(self, request):
        """Initializes the lookup parameters from the HTTP request."""
        # TODO(claudiu) Add support for URLs of the type:
        # http://mlab-ns.appspot.com/tool-name/ipv6
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
            lat_long = request.headers[message.HEADER_LAT_LONG]
            try:
                self.latitude, self.longitude = [
                    float(x) for x in lat_long.split(',')]
            except ValueError:
                # TODO(claudiu) Use geolocation data from Maxmind.
                logging.error('Bad geo coordinates %s', lat_long)

    def is_policy_geo(self):
        return (self.policy == message.POLICY_GEO)

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
            "AND status = :status "
            "AND update_request_timestamp > :timestamp ",
            tool_id=lookup_query.tool_id,
            status=message.STATUS_ONLINE,
            timestamp=oldest_timestamp)
            # TODO (claudiu) Check ipv6/ipv4.
        return candidates.fetch(constants.MAX_FETCHED_RESULTS)

    def answer_query(self, query):
        """Selects the geographically closest SliverTool.

        Args:
            query: A LookupQuery instance.

        Return:
            A SliverTool entity in case of success, or None if there is no
            SliverTool available that matches the query.
        """
        sliver_tools = self.get_sliver_tool_candidates(query)
        if not sliver_tools:
            logging.error('No results found for %s.', query.tool_id)
            return None

        min_distance = float('+inf')
        closest_sliver_tools = []
        distances = {}

        # Compute for each SliverTool the distance and add the SliverTool
        # to the 'closest_sliver_tools' list if the computed  distance is
        # less(or equal) then the current minimum.
        # To avoid computing the distances twice, cache the results in
        # a dict.
        for sliver_tool in sliver_tools:
            # Check if we already computed this distance.
            if (distances.has_key(sliver_tool.site_id)):
                current_distance = distances[sliver_tool.site_id]
            else:
                # Compute the distance and add it to the dict.
                current_distance = distance.distance(
                    query.latitude,
                    query.longitude,
                    sliver_tool.latitude,
                    sliver_tool.longitude)
                distances[sliver_tool.site_id] = current_distance

            # Update the min distance and add the SliverTool to the list.
            if (current_distance <= min_distance):
                min_distance = current_distance
                closest_sliver_tools.insert(0, sliver_tool)

        # Sort the 'closest_sliver_tools' list by distance and select only
        # those within an acceptable range. Then return one of these,
        # chosen randomly.
        best_sliver_tools = []
        distance_range = min_distance * constants.EPSILON
        for sliver_tool in closest_sliver_tools:
            if  distances[sliver_tool.site_id] <= distance_range:
                best_sliver_tools.append(sliver_tool)
            else:
                break

        return random.choice(best_sliver_tools)

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
            "AND status = :status "
            "AND update_request_timestamp > :timestamp "
            "AND site_id in :site_id_list ",
            tool_id=query.tool_id,
            status=message.STATUS_ONLINE,
            timestamp=oldest_timestamp,
            site_id_list=site_id_list).fetch(constants.MAX_FETCHED_RESULTS)
            # TODO (claudiu) Check ipv6/ipv4.

        if not candidates:
            return None

        return random.choice(candidates)
