from functools import partial
import logging

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message

from google.appengine.api import memcache


def _filter_by_status(tools, address_family, status):
    """Filter sliver tools based on the status of their available interfaces.

    Args:
        tools: A list of sliver tools to filter by status.
        address_family: Address family of the interface to which the status
            parameter applies. If None, include tools that have the given
            status on any interface.
        status: Tool status to filter for (i.e. only return tools with this
            status).

    Returns:
        A subset of the provided tools, filtered by status.
    """
    status_attrs = []
    if address_family == message.ADDRESS_FAMILY_IPv4:
        status_attrs.append('status_ipv4')
    elif address_family == message.ADDRESS_FAMILY_IPv6:
        status_attrs.append('status_ipv6')
    else:
        # When caller has not specified an address family, use any interface
        status_attrs.append('status_ipv4')
        status_attrs.append('status_ipv6')

    filtered = []
    for tool in tools:
        for status_attr in status_attrs:
            if getattr(tool, status_attr) == status:
                filtered.append(tool)
                # Exit as soon as the tool matches any set of criteria
                break
    return filtered


def _filter_by_country(tools, country):
    """Filters sliver tools based on the tool's country."""
    return filter(lambda t: t.country == country, tools)


def _filter_choose_one_host_per_site(tools):
    """Filters to make sure only one host is returned per site_id.

    This filter should be run after _filter_by_status if you want to make sure
    the chosen site is up.

    Args:
        tools: The list of tools to filter.

    Returns:
        A list containing a unique tool for each site.
    """
    sites = {}
    for tool in tools:
        if tool.site_id not in sites:
            sites[tool.site_id] = tool
        else:
            sites[tool.site_id] = min(sites[tool.site_id],
                                      tool,
                                      key=lambda t: t.fqdn)
    return [tool for tool in sites.values()]


def _find_site_ids_for_metro(metro):
    """Determine which site IDs are present in a given metro.

    Args:
        metro: The metro for which to find site IDs.

    Returns:
        A list of site IDs for the given metro.
    """
    sites = model.Site.all().filter('metro =', metro).fetch(
        constants.MAX_FETCHED_RESULTS)

    if not sites:
        logging.warning('No results found for metro %s.', metro)
        return []

    logging.info('Found %d results for metro %s.', len(sites), metro)
    return [s.site_id for s in sites]


class ToolProperties(object):
    """A set of criteria to specify matching SliverTool(s)."""

    def __init__(self,
                 tool_id,
                 status=None,
                 address_family=None,
                 metro=None,
                 country=None):
        self.tool_id = tool_id
        self.status = status
        self.address_family = address_family
        self.metro = metro
        self.country = country

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)


class ToolFetcher(object):
    """Fetches SliverTools from AppEngine memcache and Datastore."""

    def __init__(self):
        self._memcache_fetcher = ToolFetcherMemcache()
        self._datastore_fetcher = ToolFetcherDatastore()

    def fetch(self, tool_properties):
        """Fetch SliverTool objects with specified criteria.

        Retrieves SliverTool objects with matching criteria. Tries to retrieve
        from memcache first, but fails over to Datastore if memcache has no
        matches.

        Args:
            tool_properties: A set of criteria that specifies what subset of
                SliverTools to retrieve from the Datastore.

        Returns:
            A list of SliverTool objects that match the specified criteria.
        """
        results = self._memcache_fetcher.fetch(tool_properties)
        if results:
            return results

        logging.info(
            'Sliver tools not found in memcache, falling back to data store.')
        return self._datastore_fetcher.fetch(tool_properties)


class ToolFetcherMemcache(object):
    """Fetches SliverTool objects from the AppEngine Memcache."""

    def fetch(self, tool_properties):
        """Fetch SliverTool objects from the Memcache with specified criteria.

        Args:
            tool_properties: A set of criteria that specifies what subset of
                SliverTools to retrieve from Memcache.

        Returns:
            A list of SliverTool objects that match the specified criteria.
        """
        tool_filters = []
        if tool_properties.status:
            tool_filters.append(
                partial(_filter_by_status,
                        address_family=tool_properties.address_family,
                        status=tool_properties.status))
        if tool_properties.country:
            tool_filters.append(
                partial(_filter_by_country,
                        country=tool_properties.country))
        if tool_properties.metro:
            # Can't filter by metro without hitting the Datastore because
            # Memcache does not have metro -> site ID mapping.
            return []
        tool_filters.append(_filter_choose_one_host_per_site)

        sliver_tools = memcache.get(
            tool_properties.tool_id,
            namespace=constants.MEMCACHE_NAMESPACE_TOOLS)
        if sliver_tools:
            logging.info('Sliver tools found in memcache (%d results).',
                         len(sliver_tools))

            candidates = sliver_tools
            for tool_filter in tool_filters:
                candidates = tool_filter(candidates)

            logging.info('After filtering, %d candidates match criteria.',
                         len(candidates))
            return candidates
        return []


class ToolFetcherDatastore(object):
    """Fetches SliverTool objects from the AppEngine Datastore."""

    def fetch(self, tool_properties):
        """Fetch SliverTool objects from the Datastore with specified criteria.

        Args:
            tool_properties: A set of criteria that specifies what subset of
                SliverTools to retrieve from the Datastore.

        Returns:
            A list of SliverTool objects that match the specified criteria.
        """
        gql_clauses = ['tool_id = :tool_id']
        if tool_properties.metro:
            site_ids = _find_site_ids_for_metro(tool_properties.metro)
            gql_clauses.append('site_id in :site_ids')
        else:
            site_ids = None
        if tool_properties.country:
            gql_clauses.append('country = :country')

        gql = 'WHERE ' + ' AND '.join(gql_clauses)

        gql_query = model.SliverTool.gql(
            gql,
            tool_id=tool_properties.tool_id,
            status=tool_properties.status,
            site_ids=site_ids,
            country=tool_properties.country)
        results = gql_query.fetch(constants.MAX_FETCHED_RESULTS)

        # GQL doesn't have an OR operator, which makes it impossible to write
        # GQL like (status_ipv4 = 'online' OR status_ipv6 = 'online') so we do
        # status filtering in application code.
        if tool_properties.status:
            results = _filter_by_status(
                results, tool_properties.address_family, tool_properties.status)
        results = _filter_choose_one_host_per_site(results)

        logging.info('%d sliver tools found in Datastore.', len(results))
        return results
