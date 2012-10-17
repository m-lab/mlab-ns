from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import distance
from mlabns.util import message
from mlabns.util import maxmind

import logging
import random
import socket
import time

AF_IPV4 = 'ipv4'
AF_IPV6 = 'ipv6'

class LookupQuery:
    def __init__(self):
        self.tool_id = None
        self.policy = None
        self.metro = None
        self.ip_address = None
        self.address_family = None
        self.city = None
        self.country = None
        self.latitude = None
        self.longitude = None
        self.geolocation_type = constants.GEOLOCATION_APP_ENGINE
        self.response_format = None

    def initialize_from_http_request(self, request):
        """Initializes the lookup parameters from the HTTP request.

        Args:
            request: An instance of google.appengine.webapp.Request.
        """
        self.tool_id = request.path.strip('/').split('/')[0]
        self.response_format = request.get(message.RESPONSE_FORMAT)
        self.set_ip_address(request)
        self.set_address_family(request, self.ip_address)
        self.metro = request.get(message.METRO)
        self.set_policy(request, self.metro)

        if self.policy == message.POLICY_COUNTRY:
            self.country = request.get(message.COUNTRY)
        elif self.policy == message.POLICY_GEO:
            self.set_geolocation(request)

    def set_ip_address(self, request):
        # Check if the request specifies the ip address
        # as a query string argument, otherwise use the client's
        # remote address.
        input_ip_address = request.get(message.REMOTE_ADDRESS)
        if input_ip_address:
            self.ip_address = input_ip_address
        else:
            self.ip_address = request.remote_addr

    def set_address_family(self, request, input_ip_address):
        # Check if the request specifies the ip address family
        # as a query string argument, otherwise infer address
        # family from ip_address.
        input_address_family = request.get(message.ADDRESS_FAMILY)
        if (input_address_family == message.ADDRESS_FAMILY_IPv4 or
            input_address_family == message.ADDRESS_FAMILY_IPv6):
            self.address_family = input_address_family
        else:
            try:
                socket.inet_pton(socket.AF_INET6, input_ip_address)
                self.address_family = message.ADDRESS_FAMILY_IPv6
            except socket.error:
                self.address_family = message.ADDRESS_FAMILY_IPv4

    def set_policy(self, request, input_metro):
        valid_policies = [
            message.POLICY_METRO,
            message.POLICY_GEO,
            message.POLICY_RANDOM,
            message.POLICY_COUNTRY]
        input_policy = request.get(message.POLICY)
        if input_policy in valid_policies:
            self.policy = input_policy
        elif input_metro:
            self.policy = message.POLICY_METRO
        else:
            # TODO(claudiu): Discuss the default policy.
            self.policy = message.POLICY_GEO

    def set_geolocation(self, request):
        input_latitude = request.get(message.LATITUDE)
        input_longitude = request.get(message.LONGITUDE)
        input_city = request.get(message.CITY)
        input_country = request.get(message.COUNTRY)
        input_ip_address = request.get(message.REMOTE_ADDRESS)
        try:
            self.latitude = float(input_latitude)
            self.longitude = float(input_longitude)
            self.geolocation_type = constants.GEOLOCATION_USER_DEFINED
        except ValueError:
            if input_country or input_ip_address:
                self.geolocation_type = constants.GEOLOCATION_MAXMIND
                self.set_maxmind_geolocation(
                    input_country, input_city, input_ip_address)
            else:
                self.geolocation_type = constants.GEOLOCATION_APP_ENGINE
                self.set_appengine_geolocation(request)

    def set_maxmind_geolocation(
        self, input_country, input_city, input_ip_address):
        """Adds geolocation info using the data from MaxMind."""

        if input_country and input_city:
            geo_record = maxmind.get_city_geolocation(
                input_city, input_country)
        elif input_city:
            geo_record = maxmind.get_country_geolocation(input_city)
        else:
            geo_record = maxmind.get_ip_geolocation(input_ip_address)
        self.city = geo_record.city
        self.country = geo_record.country
        self.latitude = geo_record.latitude
        self.longitude = geo_record.longitude

    def set_appengine_geolocation(self, request):
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
        if message.HEADER_LAT_LONG in request.headers:
            lat_long = request.headers[message.HEADER_LAT_LONG]
            try:
                self.latitude, self.longitude = [
                    float(x) for x in lat_long.split(',')]
            except ValueError:
                # Log the error and use maxmind.
                logging.error('Bad geo coordinates %s', lat_long)
                self.set_maxmind_geolocation(
                    request, self.country, self.city, self.ip_address)

class ResolverBase:
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
            return self._get_candidates(query, AF_IPV6)
        return self._get_candidates(query, AF_IPV4)

    def _get_candidates(self, query, address_family):
        # First try to get the sliver tools from the cache.
        sliver_tools = memcache.get(query.tool_id)
        if sliver_tools:
            logging.info(
                'Sliver tools found in memcache (%s results).',
                len(sliver_tools))
            candidates = []
            for sliver_tool in sliver_tools:
                if  ((address_family == AF_IPV4 and
                    sliver_tool.status_ipv4 == message.STATUS_ONLINE) or
                     (address_family == AF_IPV6 and
                    sliver_tool.status_ipv6 == message.STATUS_ONLINE)):
                    candidates.append(sliver_tool)

            return candidates

        logging.info('Sliver tools not found in memcache.')
        # Get the sliver tools from from datastore.
        status_field = 'status_' + address_family
        candidates = model.SliverTool.gql(
            'WHERE tool_id = :tool_id '
            'AND ' + status_field + ' = :status',
            tool_id=query.tool_id,
            status=message.STATUS_ONLINE)

        logging.info(
            'Found (%s candidates)', candidates.count())
        return candidates.fetch(constants.MAX_FETCHED_RESULTS)

    def answer_query(self, query):
        pass


class GeoResolver(ResolverBase):
    """Chooses the server geographically closest to the client."""

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

        if not query.latitude or not query.longitude:
            logging.warning(
                'No geolocation info, returning a random sliver tool')
            return random.choice(candidates)

        logging.info('Found %s candidates.', len(candidates))
        min_distance = float('+inf')
        closest_sliver_tools = []
        distances = {}

        # Compute for each SliverTool the distance and add the SliverTool
        # to the 'closest_sliver_tools' list if the computed  distance is
        # less (or equal) than the current minimum.
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

class MetroResolver(ResolverBase):
    """Implements the metro policy."""

    def _get_candidates(self, query, address_family=AF_IPV4):
        # TODO(claudiu) Test whether the following query works as expected:
        # sites = model.Site.gql("WHERE metro = :metro", metro=query.metro)
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

        status_field = 'status_' + address_family
        # TODO(claudiu) Use the memcache.
        candidates = model.SliverTool.gql(
            'WHERE tool_id = :tool_id '
            'AND ' + status_field + ' = :status '
            'AND site_id in :site_id_list',
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

class RandomResolver(ResolverBase):
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


class CountryResolver(ResolverBase):
    """Returns a server in a specified country."""

    def answer_query(self, query):
        """Returns a SliverTool in a specified country.

        Args:
            query: A LookupQuery instance.

        Returns:
            A SliverTool entity if available, None otherwise.
        """
        if not query.country:
            return None

        candidates = self.get_candidates(query)
        if not candidates:
            logging.error('No results found for %s.', query.tool_id)
            return None

        country_candidates = []
        for candidate in candidates:
            if candidate.country == query.country:
                country_candidates.append(candidate)

        if not country_candidates:
            return None
        return random.choice(country_candidates)


def new_resolver(policy):
    if policy == message.POLICY_GEO:
        return GeoResolver()
    elif policy == message.POLICY_METRO:
        return MetroResolver()
    elif policy == message.POLICY_RANDOM:
        return RandomResolver()
    elif policy == message.POLICY_COUNTRY:
        return CountryResolver()
    else:
        return RandomResolver()
