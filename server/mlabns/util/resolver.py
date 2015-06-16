import logging
import random

from mlabns.db import tool_fetcher
from mlabns.util import distance
from mlabns.util import message


def _tool_properties_from_query(query):
    """Create ToolProperties from a LookupQuery.

    Creates a ToolProperties object for use with a resolver, based on a
    LookupQuery. Note that it only initializes common properties shared
    by all resolvers (e.g. status, tool_id) whereas resolver-specific properties
    (e.g. country, metro) are not initialized here.

    Args:
        query: LookupQuery from which to create ToolProperties

    Returns:
        A ToolProperties object initialized from the query provided.
    """
    tool_properties = tool_fetcher.ToolProperties(
        tool_id=query.tool_id, status=message.STATUS_ONLINE)
    if query.tool_address_family:
        tool_properties.address_family = query.tool_address_family
    return tool_properties


class ResolverBase(object):
    """Resolver base class."""

    def __init__(self):
        self.tool_fetcher = tool_fetcher.ToolFetcher()

    def _get_matching_candidates(self, query):
        tool_properties = _tool_properties_from_query(query)
        return self._fetch_tools_with_properties(tool_properties)

    def _fetch_tools_with_properties(self, tool_properties):
        candidates = self.tool_fetcher.fetch(tool_properties)
        if not candidates:
            logging.error('No results found for %s.', tool_properties.tool_id)
            return None
        return candidates


class AllResolver(ResolverBase):

    def answer_query(self, query):
        return self._get_matching_candidates(query)


class GeoResolver(ResolverBase):
    """Chooses the server geographically closest to the client."""

    def _get_closest_n_candidates(self, query, max_results):
        """Selects the top N geographically closest SliverTools to the client.

        Args:
            query: A LookupQuery instance.
            max_results: The maximum number of candidates to return.

        Returns:
            A list of SliverTool entities on success, or None if there is no
            SliverTool available that matches the query.
        """
        candidates = self._get_matching_candidates(query)
        if not candidates:
            return None

        if (query.latitude is None) or (query.longitude is None):
            logging.warning(
                'No latitude/longitude, return random sliver tool(s).')
            return random.sample(candidates, min(len(candidates), max_results))

        # Pre-shuffle the candidates to randomize the order of equidistant
        # results.
        random.shuffle(candidates)

        site_distances = {}
        tool_distances = []
        for candidate in candidates:
            if candidate.site_id not in site_distances:
                site_distances[candidate.site_id] = distance.distance(
                    query.latitude, query.longitude, candidate.latitude,
                    candidate.longitude)
            tool_distances.append(
                {'distance': site_distances[candidate.site_id],
                 'tool': candidate})

        # Sort the tools by distance
        tool_distances.sort(key=lambda t: t['distance'])

        # Create a new list of just the sorted SliverTool objects.
        sorted_tools = [t['tool'] for t in tool_distances]
        return sorted_tools[:max_results]

    def answer_query(self, query):
        """Selects the geographically closest SliverTool.

        Args:
            query: A LookupQuery instance.

        Returns:
            A single-element list of SliverTools in case of success, or None if
            there is no SliverTool available that matches the query.
        """
        return self._get_closest_n_candidates(query, 1)


class GeoResolverWithOptions(GeoResolver):
    """Chooses the N geographically closest servers to the client."""

    def answer_query(self, query):
        """Selects the top N geographically closest SliverTools to the client.

        Finds the top N closest SliverTools to the client and returns them.
        Note that N is currently hardcoded to 4.

        Args:
            query: A LookupQuery instance.

        Returns:
            A list of SliverTools on success, or None if there is no SliverTool
            available that matches the query.
        """
        # TODO(mtlynch): N is currently hardcoded to 4 here due to concern that
        # changing the value would break compatibility with uTorrent clients. If
        # uTorrent clients can gracefully handle responses where n=1, we should
        # get rid of GeoResolverWithOptions and just use GeoResolver.
        return self._get_closest_n_candidates(query, 4)


class MetroResolver(ResolverBase):
    """Implements the metro policy."""

    def _get_matching_candidates(self, query):
        tool_properties = _tool_properties_from_query(query)
        tool_properties.metro = query.metro
        return self._fetch_tools_with_properties(tool_properties)

    def answer_query(self, query):
        """Returns a SliverTool in a specified metro.

        Args:
            query: A LookupQuery instance.

        Returns:
            A single-element list of SliverTools if a valid match exists, None
            otherwise.
        """
        if not query.metro:
            return None

        candidates = self._get_matching_candidates(query)
        if not candidates:
            return None

        return [random.choice(candidates)]


class RandomResolver(ResolverBase):
    """Returns a server chosen randomly."""

    def answer_query(self, query):
        """Selects a random sliver tool among the available candidates.

        Args:
            query: A LookupQuery instance.

        Returns:
            A single-element list of SliverTools if a valid match exists, None
            otherwise.
        """
        candidates = self._get_matching_candidates(query)
        if not candidates:
            return None

        return [random.choice(candidates)]


class CountryResolver(ResolverBase):
    """Returns a server in a specified country."""

    def _get_matching_candidates(self, query):
        tool_properties = _tool_properties_from_query(query)
        tool_properties.country = query.country
        return self._fetch_tools_with_properties(tool_properties)

    def answer_query(self, query):
        """Returns a SliverTool in a specified country.

        Args:
            query: A LookupQuery instance.

        Returns:
            A single-element list of SliverTools if a valid match exists, None
            otherwise.
        """
        if not query.country:
            return None

        candidates = self._get_matching_candidates(query)
        if not candidates:
            return None

        return [random.choice(candidates)]


def new_resolver(policy):
    if policy == message.POLICY_GEO:
        return GeoResolver()
    elif policy == message.POLICY_METRO:
        return MetroResolver()
    elif policy == message.POLICY_RANDOM:
        return RandomResolver()
    elif policy == message.POLICY_COUNTRY:
        return CountryResolver()
    elif policy == message.POLICY_GEO_OPTIONS:
        return GeoResolverWithOptions()
    elif policy == message.POLICY_ALL:
        return AllResolver()
    else:
        return RandomResolver()
