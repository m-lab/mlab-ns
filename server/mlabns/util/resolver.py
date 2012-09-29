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
        self.address_family = message.ADDRESS_FAMILY_IPv4
        self.city = None
        self.country = None
        self.latitude = None
        self.longitude = None
        self.response_format = None

    @property
    def policy_geo(self):
        return self.policy == message.POLICY_GEO

    @property
    def policy_metro(self):
        return self.policy == message.POLICY_METRO

    @property
    def has_geolocation(self):
        return (self.latitude is not None and self.longitude is not None)

    def initialize_from_dictionary(self, dictionary):
        """Inizializes the lookup parameters from a dictionary.

        Args:
            dictionary: A dict containing the query configuration.
        """
        if message.REMOTE_ADDRESS in dictionary:
            self.ip_address = dictionary[message.REMOTE_ADDRESS]

        if message.POLICY in dictionary:
            self.policy = dictionary[message.POLICY]

        if message.RESPONSE_FORMAT in dictionary:
            self.response_format = dictionary[message.RESPONSE_FORMAT]

        if message.METRO in dictionary:
            self.metro = dictionary[message.METRO]
            self.policy = message.POLICY_METRO

        if message.COUNTRY in dictionary:
            self.country = dictionary[message.COUNTRY]

        if message.CITY in dictionary:
            self.city = dictionary[message.CITY]

        if message.ADDRESS_FAMILY in dictionary:
            address_family = dictionary[message.ADDRESS_FAMILY]
            if (address_family == message.ADDRESS_FAMILY_IPv4 or
                address_family == message.ADDRESS_FAMILY_IPv6):
                self.address_family = address_family

        # Default to geo policy.
        if not self.policy:
            self.policy = message.POLICY_GEO

        if self.address_family is None:
            try:
                socket.inet_pton(socket.AF_INET6, self.ip_address)
                self.address_family = message.ADDRESS_FAMILY_IPv6
            except socket.error:
                self.address_family = message.ADDRESS_FAMILY_IPv4

        self.add_maxmind_geolocation()

        # If there is no geolocation data, set the policy to random.
        if not self.has_geolocation:
            self.policy = message.POLICY_RANDOM

    def initialize_from_http_request(self, request):
        """Initializes the lookup parameters from the HTTP request.

        Args:
            request: An instance of google.appengine.webapp.Request.
        """
        parts = request.path.strip('/').split('/')
        self.tool_id = parts[0]

        self.ip_address = request.remote_addr
        self.policy = request.get(message.POLICY)
        self.metro = request.get(message.METRO)
        self.response_format = request.get(message.RESPONSE_FORMAT)
        self.city = request.get(message.CITY)
        self.country = request.get(message.COUNTRY)

        address_family = request.get(message.ADDRESS_FAMILY)
        if (address_family == message.ADDRESS_FAMILY_IPv4 or
            address_family == message.ADDRESS_FAMILY_IPv6):
            self.address_family = address_family

        if self.metro:
            self.policy = message.POLICY_METRO

        # Default to geo policy.
        if not self.policy:
            self.policy = message.POLICY_GEO

        if self.address_family is None:
            try:
                socket.inet_pton(socket.AF_INET6, self.ip_address)
                self.address_family = message.ADDRESS_FAMILY_IPv6
            except socket.error:
                self.address_family = message.ADDRESS_FAMILY_IPv4

        if self.country and self.country != constants.UNKNOWN_COUNTRY:
            self.add_maxmind_geolocation()
        elif message.HEADER_LAT_LONG in request.headers:
            self.add_appengine_geolocation(request)
        else:
            self.add_maxmind_geolocation()

        # If there is no geolocation data, set the policy to random.
        if not self.has_geolocation:
            self.policy = message.POLICY_RANDOM

    def add_maxmind_geolocation(self):
        """Adds geolocation info using the data from MaxMind."""
        if self.country and self.city:
            geo_record = maxmind.get_city_geolocation(
                self.city, self.country)
        elif self.country:
            geo_record = maxmind.get_country_geolocation(self.country)
        else:
            geo_record = maxmind.get_ip_geolocation(self.ip_address)
        self.city = geo_record.city
        self.country = geo_record.country
        self.latitude = geo_record.latitude
        self.longitude = geo_record.longitude

    def add_appengine_geolocation(self, request):
        """Adds geolocation info using the data provided by AppEngine.

        If the geolocation info is not included in the headers, it will
        use the data from MaxmindCityLocation/MaxmindCityBlock.

        Args:
            request: A webapp.Request instance.
        """
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

    def is_valid_address_family(self, address_family):
        """Validates the 'address_family' argument in the query string.

        Args:
            address_family: A string describing the IP address family.
                Currently the accepted values are 'ipv4' or 'ipv6'.

        Returns:
            True if address_family is 'ipv4' or 'ipv6', False otherwise.
        """
        return (address_family == message.ADDRESS_FAMILY_IPv4 or
                address_family == message.ADDRESS_FAMILY_IPv6)


class Resolver:
    """Resolver base class."""

    def get_candidates(self, query):
        """Find candidates for server selection.

        Args:
            query: A LookupQuery instance.

        Returns:
            A list of SliverTool entities that match the requirements
            specified in the 'query'.
        """
        if query.address_family == message.ADDRESS_FAMILY_IPv6:
            return self.get_candidates_ipv6(lookup_query)

        return self.get_candidates_ipv4(query)

    def get_candidates_ipv4(self, query):
        """Find candidates for server selection.

        Args:
            query: A LookupQuery instance.

        Returns:
            A list of SliverTool entities that match the requirements
            specified in the 'lookup_query'.
        """
        # First try to get the sliver tools from the cache.
        sliver_tools = memcache.get(query.tool_id)
        if sliver_tools is not None:
            logging.info(
                'Sliver tools found in memcache (%s results).',
                len(sliver_tools.keys()))
            candidates = []
            for sliver_tool in sliver_tools.values():
                if (sliver_tool.status_ipv4 == message.STATUS_ONLINE):
                    candidates.append(sliver_tool)
            return candidates

        logging.info('Sliver tools not found in memcache.')
        # Get the sliver tools from from datastore.
        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status_ipv4 = :status",
            tool_id=query.tool_id,
            status=message.STATUS_ONLINE)

        logging.info(
            'Found (%s candidates)', candidates.count())
        return candidates.fetch(constants.MAX_FETCHED_RESULTS)

    def get_candidates_ipv6(self, query):
        """Finds candidates for server selection.

        Args:
            query: A LookupQuery instance.

        Returns:
            A list of SliverTool entities that match the requirements
            specified in the 'query'.
        """
        # First try to get the sliver tools from the cache.
        sliver_tools = memcache.get(query.tool_id)
        if sliver_tools is not None:
            logging.info(
                'Sliver tools found in memcache (%s results).',
                len(sliver_tools))
            candidates = []
            for sliver_tool in sliver_tools.values():
                if (sliver_tool.status_ipv6 == message.STATUS_ONLINE):
                    candidates.append(sliver_tool)
            return candidates

        logging.info('Sliver tools not found in memcache.')
        # Get the sliver tools from from datastore.
        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status_ipv6 = :status",
            tool_id=query.tool_id,
            status=message.STATUS_ONLINE)
        return candidates.fetch(constants.MAX_FETCHED_RESULTS)

    def answer_query(self, query):
        pass


class GeoResolver(Resolver):
    """Implements the closest-node policy."""

    def answer_query(self, query):
        """Selects the geographically closest SliverTool.

        Args:
            query: A LookupQuery instance.

        Returns:
            A SliverTool entity in case of success, or None if there is no
            SliverTool available that matches the query.
        """
        candidates = self.get_candidates(query)
        if not candidates:
            logging.error('No results found for %s.', query.tool_id)
            return None

        logging.info('Found %s candidates.', len(candidates))
        min_distance = float('+inf')
        closest_sliver_tools = []
        distances = {}

        # Compute for each SliverTool the distance and add the SliverTool
        # to the 'closest_sliver_tools' list if the computed  distance is
        # less(or equal) then the current minimum.
        # To avoid computing the distances twice, cache the results in
        # a dict.
        for sliver_tool in candidates:
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
        distance_range = min_distance
        for sliver_tool in closest_sliver_tools:
            if  distances[sliver_tool.site_id] <= distance_range:
                best_sliver_tools.append(sliver_tool)
            else:
                break

        return random.choice(best_sliver_tools)

class MetroResolver(Resolver):
    """Implements the metro policy."""

    def get_candidates_ipv4(self, query):
        sites = model.Site.all().filter("metro =", query.metro).fetch(
            constants.MAX_FETCHED_RESULTS)

        logging.info(
            'Found %s results for metro %s.', len(sites), query.metro)
        if not sites:
            logging.info('No results found for metro %s.', query.metro)
            return None

        site_id_list = []
        for site in sites:
            site_id_list.append(site.site_id)

        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status_ipv4 = :status "
            "AND site_id in :site_id_list",
            tool_id=query.tool_id,
            status=message.STATUS_ONLINE,
            site_id_list=site_id_list).fetch(constants.MAX_FETCHED_RESULTS)

        return candidates

    def get_candidates_ipv6(self, query):
        sites = model.Site.all().filter("metro =", query.metro).fetch(
            constants.MAX_FETCHED_RESULTS)

        logging.info(
            'Found %s results for metro %s.', len(sites), query.metro)
        if not sites:
            logging.info('No results found for metro %s.', query.metro)
            return None

        site_id_list = []
        for site in sites:
            site_id_list.append(site.site_id)

        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status_ipv6 = :status "
            "AND site_id in :site_id_list",
            tool_id=query.tool_id,
            status=message.STATUS_ONLINE,
            site_id_list=site_id_list).fetch(constants.MAX_FETCHED_RESULTS)

        return candidates

    def answer_query(self, query):
        """Selects randomly a sliver tool that matches the 'metro'.

        Args:
            query: A LookupQuery instance.

        Returns:
            A SliverTool entity that matches the 'metro' if available,
            and None otherwise.
        """
        candidates = self.get_candidates(query)
        if not candidates:
            logging.error('No results found for %s.', query.tool_id)
            return None

        return random.choice(candidates)

class RandomResolver(Resolver):
    """Returns a server chosen randomly."""

    def answer_query(self, query):
        """Returns a randomly chosen SliverTool.

        Args:
            query: A LookupQuery instance.

        Returns:
            A SliverTool entity if available, None otherwise.
        """
        candidates = self.get_candidates(query)
        if not candidates:
            logging.error('No results found for %s.', query.tool_id)
            return None

        return random.choice(candidates)
