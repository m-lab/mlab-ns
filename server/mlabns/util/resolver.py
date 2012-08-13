from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import distance
from mlabns.util import message
from mlabns.util.geo import maxmind

import logging
import random
import socket
import time

class LookupQuery:
    def __init__(self):
        self.tool_id = None
        self.policy = message.POLICY_GEO
        self.metro = None
        self.ip_address = None
        self.ipv6_flag = None
        self.city = None
        self.country = None
        self.latitude = 0.0
        self.longitude = 0.0
        self.response_format = None

    @property
    def policy_geo(self):
        return self.policy == message.POLICY_GEO

    @property
    def policy_metro(self):
        return self.policy == message.POLICY_METRO

    def initialize_from_dictionary(self, dictionary):
        """Inizializes the lookup parameters from a dictionary.

        Args:
            dictionary: A dict containing the query configuration.
        """

        # TODO(claudiu) Add support for URLs of the type:
        # http://mlab-ns.appspot.com/tool-name/ipv6.
        if message.REMOTE_ADDRESS in dictionary:
            self.ip_address = dictionary[message.REMOTE_ADDRESS]

        if message.POLICY in dictionary:
            self.policy = dictionary[message.POLICY]

        if message.RESPONSE_FORMAT in dictionary:
            self.response_format = dictionary[message.RESPONSE_FORMAT]

        if message.METRO in dictionary:
            self.metro = dictionary[message.METRO]
            self.policy = message.POLICY_METRO

        # Default to geo policy.
        if not self.policy:
            self.policy = message.POLICY_GEO

        try:
            socket.inet_pton(socket.AF_INET6, self.ip_address)
            self.ipv6_flag = True
        except socket.error:
            self.ipv6_flag = False

        self.add_maxmind_geolocation()

    def initialize_from_http_request(self, request):
        """Inizializes the lookup parameters from the HTTP request.

        Args:
            request: An instance of google.appengine.webapp.Request.
        """
        # TODO(claudiu) Add support for URLs of the type:
        # http://mlab-ns.appspot.com/tool-name/ipv6.
        parts = request.path.strip('/').split('/')
        self.tool_id = parts[0]

        try:
            socket.inet_pton(socket.AF_INET6, request.remote_addr)
            self.ipv6_flag = True
        except socket.error:
            self.ipv6_flag = False

        self.ip_address = request.remote_addr
        self.policy = request.get(message.POLICY)
        self.metro = request.get(message.METRO)
        self.response_format = request.get(message.RESPONSE_FORMAT)

        if self.metro:
            self.policy = message.POLICY_METRO

        # Default to geo policy.
        if not self.policy:
            self.policy = message.POLICY_GEO

        if message.HEADER_LAT_LONG in request.headers:
            self.add_appengine_geolocation(request)
        else:
            self.add_maxmind_geolocation()

    def add_maxmind_geolocation(self):
        geo_record = maxmind.get_ip_geolocation(self.ip_address)
        self.city = geo_record.city
        self.country = geo_record.country
        self.latitude = geo_record.latitude
        self.longitude = geo_record.longitude

    def add_appengine_geolocation(self, request):
        if message.HEADER_CITY in request.headers:
            self.city = request.headers[message.HEADER_CITY]
        if message.HEADER_COUNTRY in request.headers:
            self.country = request.headers[message.HEADER_COUNTRY]
        lat_long = request.headers[message.HEADER_LAT_LONG]
        try:
            self.latitude, self.longitude = [
                float(x) for x in lat_long.split(',')]
        except ValueError:
            # Log the error and use maxmind.
            logging.error('Bad geo coordinates %s', lat_long)
            self.add_maxmind_geolocation(request)

class GeoResolver:
    """Implements the closest-node policy."""

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

        logging.debug('Sliver tools not found in memcache')
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

        Returns:
            A SliverTool entity in case of success, or None if there is no
            SliverTool available that matches the query.
        """
        sliver_tools = self.get_sliver_tool_candidates(query)
        if not sliver_tools:
            logging.error('No results found for %s.', query.tool_id)
            return None

        logging.info('Found %s candidates.', len(sliver_tools))
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
                current_distance = distance.distance(
                    query.latitude,
                    query.longitude,
                    sliver_tool.latitude,
                    sliver_tool.longitude)

                # Update the dict.
                if sliver_tool.site_id not in distances:
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
