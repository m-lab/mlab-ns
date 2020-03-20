import logging
import random

from mlabns.db import sliver_tool_fetcher
from mlabns.util import distance
from mlabns.util import message
from mlabns.db import client_signature_fetcher


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
    tool_properties = sliver_tool_fetcher.ToolProperties(
        tool_id=query.tool_id,
        status=message.STATUS_ONLINE)
    if query.tool_address_family:
        tool_properties.address_family = query.tool_address_family
    return tool_properties


class ResolverBase(object):
    """Resolver base class."""

    def __init__(self, client_signature=''):
        self.sliver_tool_fetcher = sliver_tool_fetcher.SliverToolFetcher()
        self.client_signature = client_signature

    def _get_matching_candidates(self, query):
        tool_properties = _tool_properties_from_query(query)
        return self._fetch_tools_with_properties(tool_properties)

    def _fetch_tools_with_properties(self, tool_properties):
        candidates = self.sliver_tool_fetcher.fetch(tool_properties)
        if not candidates:
            logging.error('No results found for %s.', tool_properties.tool_id)
            return None
        return candidates


class AllResolver(ResolverBase):

    def answer_query(self, query):
        return self._get_matching_candidates(query)

# site_keep_probability defines explicit probabilities for 1g sites that cannot
# handle the current number of requests. Each value is the probability of
# selecting this site. The default value is 1.0.
site_keep_probability = {
    'bom01': 0.5,
    'hnd01': 0.2,  # 0.2
    'lga1t': 0.5,
    'lis01': 0.5,
    'lju01': 0.5,
    'tnr01': 0.5,
    'tun01': 0.5,
    'vie01': 0.5,
    'yqm01': 0.5,
    'yul02': 0.2,  # 0.2
    'yvr01': 0.5,
    'ywg01': 0.5,
    'yyc02': 0.5,
    'yyz02': 0.2,  # 0.2
}


class GeoResolver(ResolverBase):
    """Chooses the server geographically closest to the client."""

    def _add_candidate(self, query, candidate, site_distances, tool_distances):
        if candidate.site_id not in site_distances:
            site_distances[candidate.site_id] = distance.distance(
                query.latitude, query.longitude, candidate.latitude,
                candidate.longitude)
            tool_distances.append({
                'distance': site_distances[candidate.site_id],
                'tool': candidate
            })

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

        filtered_candidates = []

        prob = client_signature_fetcher.ClientSignatureFetcher().fetch(
            self.client_signature)
        if random.uniform(0, 1) > prob:
            # NB: the string format makes log monitoring possible.
            logging.info('SIGNATURE_FOUND: %f returned from memcache for %s',
                         prob, self.client_signature)
            # Filter the candidates sites, only keep the '0c' sites
            filtered_candidates = filter(lambda c: c.site_id[-1] == 'c',
                                         candidates)
        else:
            # Filter the candidates sites, only keep the regular sites
            filtered_candidates = filter(lambda c: c.site_id[-1] != 'c',
                                         candidates)

        for candidate in filtered_candidates:
            prob = site_keep_probability.get(candidate.site_id, 1.0)
            if random.uniform(0, 1) < prob:
                # Only add candidate if a random probability is under the "site
                # keep probability" threshold.
                self._add_candidate(query, candidate, site_distances,
                                    tool_distances)

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


def new_resolver(policy, client_signature=''):
    if policy == message.POLICY_GEO:
        return GeoResolver(client_signature)
    elif policy == message.POLICY_METRO:
        return MetroResolver(client_signature)
    elif policy == message.POLICY_RANDOM:
        return RandomResolver(client_signature)
    elif policy == message.POLICY_COUNTRY:
        return CountryResolver(client_signature)
    elif policy == message.POLICY_GEO_OPTIONS:
        return GeoResolverWithOptions(client_signature)
    elif policy == message.POLICY_ALL:
        return AllResolver(client_signature)
    else:
        return RandomResolver(client_signature)
