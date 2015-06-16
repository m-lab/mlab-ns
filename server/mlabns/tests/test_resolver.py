import unittest

from mlabns.db import model
from mlabns.db import tool_fetcher
from mlabns.util import lookup_query
from mlabns.util import message
from mlabns.util import resolver
import mock


def _createSliverTool(tool_id, site_id=None, status_ipv4=None, status_ipv6=None,
                      latitude=None, longitude=None, country=None):
    tool = model.SliverTool()
    tool.tool_id = tool_id
    tool.site_id = site_id
    tool.status_ipv4 = status_ipv4
    tool.status_ipv6 = status_ipv6
    tool.latitude = latitude
    tool.longitude = longitude
    tool.country = country
    return tool

_TOOL_ID = 'valid_tool_id'


class ResolverTestCaseBase(unittest.TestCase):
    """Base class for common assertions among all ResolverTest classes."""

    def assertQueryResultSingleTool(self, query, mock_fetch_results,
                                    result_tool_expected,
                                    tool_properties_expected):
        """Assert that the resolver result matches expected values.

        Assert that calling resolver.answer_query returns a list with a single
        tool and that resolver fetched tools from the db using the correct
        criteria.

        Args:
            query: LookupQuery instance based on the client's query.
            mock_fetch_results: Mock results from querying the db.
            result_tool_expected: The expected winning tool that the resolver
                returns.
            tool_properties_expected: Expected tool properties that resolver
                used to retrieve tools from the db.
        """
        mock_fetch = tool_fetcher.ToolFetcher().fetch
        mock_fetch.return_value = mock_fetch_results

        query_results_expected = [result_tool_expected]
        query_results_actual = self.resolver.answer_query(query)
        self.assertSequenceEqual(query_results_expected,
                                 query_results_actual)

        mock_fetch.assert_called_with(tool_properties_expected)

    def assertQueryResultMultiTool(self, query, mock_fetch_results,
                                   query_results_expected,
                                   tool_properties_expected):
        """Assert that the resolver result matches expected values.

        Assert that calling resolver.answer_query returns a list with multiple
        tools and that resolver fetched tools from the db using the correct
        criteria.

        Args:
            query: LookupQuery instance based on the client's query.
            mock_fetch_results: Mock results from querying the db.
            query_results_expected: The expected winning tools that the resolver
                returns.
            tool_properties_expected: Expected tool properties that resolver
                used to retrieve tools from the db.
        """
        mock_fetch = tool_fetcher.ToolFetcher().fetch
        mock_fetch.return_value = mock_fetch_results

        query_results_actual = self.resolver.answer_query(query)
        self.assertSetEqual(set(query_results_expected),
                            set(query_results_actual))

        mock_fetch.assert_called_with(tool_properties_expected)

    def assertQueryResultSingleToolWithRandomChoice(
            self, query, mock_fetch_results, filtered_tool_candidates,
            tool_properties_expected):
        """Assert that the resolver result matches expected values.

        Assert that calling resolver.answer_query finds a list of tool
        candidates to return and then randomly selects a single tool as the
        winner. Also asserts that the resolver fetched tools from the db using
        the correct criteria.

        Args:
            query: LookupQuery instance based on the client's query.
            mock_fetch_results: Mock results from querying the db.
            filtered_tool_candidates: The expected candidate tools from which
                the resolver will randomly pick a winner.
            tool_properties_expected: Expected tool properties that resolver
                used to retrieve tools from the db.
        """
        mock_fetch = tool_fetcher.ToolFetcher().fetch
        mock_fetch.return_value = mock_fetch_results

        # Mock out random behavior to allow deterministic test results
        with mock.patch('random.choice') as mock_random:
            random_winner_index = 0
            mock_random.side_effect = lambda x: x[random_winner_index]

            query_results_expected = [
                filtered_tool_candidates[random_winner_index]]
            query_results_actual = self.resolver.answer_query(query)
            self.assertSequenceEqual(query_results_expected,
                                     query_results_actual)

            # Make sure that the random selection was between the expected
            # candidate tools, after any filtering
            self.assertSequenceEqual(filtered_tool_candidates,
                                     mock_random.call_args[0][0])

        mock_fetch.assert_called_with(tool_properties_expected)

    def assertQueryResultMultiToolWithRandomSample(
            self, query, mock_fetch_results, filtered_tool_candidates,
            sample_size, tool_properties_expected):
        """Assert that the resolver result matches expected values.

        Assert that calling resolver.answer_query finds a list of tool
        candidates to return and then randomly selects a single tool as the
        winner. Also asserts that the resolver fetched tools from the db using
        the correct criteria.

        Args:
            query: LookupQuery instance based on the client's query.
            mock_fetch_results: Mock results from querying the db.
            filtered_tool_candidates: The expected candidate tools from which
                the resolver will randomly pick a winner.
            sample_size: The number of randomly selected elements expected in
                the final result.
            tool_properties_expected: Expected tool properties that resolver
                used to retrieve tools from the db.
        """
        mock_fetch = tool_fetcher.ToolFetcher().fetch
        mock_fetch.return_value = mock_fetch_results

        # Mock out random behavior to allow deterministic test results
        with mock.patch('random.sample') as mock_random:
            # Make random.sample yield the k last elements of the set
            mock_random.side_effect = lambda x, k: x[-k:]

            query_results_expected = filtered_tool_candidates[-sample_size:]
            query_results_actual = self.resolver.answer_query(query)
            self.assertSequenceEqual(query_results_expected,
                                     query_results_actual)

            # Make sure that the random selection was between the expected
            # candidate tools, after any filtering
            self.assertSequenceEqual(filtered_tool_candidates,
                                     mock_random.call_args[0][0])

        mock_fetch.assert_called_with(tool_properties_expected)

    def assertQueryResultWithRandomShuffle(self, query, mock_fetch_results,
            query_results_expected, tool_properties_expected):
        """Assert that the resolver result matches expected values.

        Assert that calling resolver.answer_query finds a list of tool
        candidates to return and then randomly selects a subset of those tools
        as the winners. Also asserts that the resolver fetched tools from the db
        using the correct criteria.

        Args:
            query: LookupQuery instance based on the client's query.
            mock_fetch_results: Mock results from querying the db.
            query_results_expected: Expected results from calling
                resolver.answer_query().
            tool_properties_expected: Expected tool properties that resolver
                used to retrieve tools from the db.
        """
        mock_fetch = tool_fetcher.ToolFetcher().fetch
        mock_fetch.return_value = mock_fetch_results

        # Mock out random behavior to allow deterministic test results
        with mock.patch('random.shuffle') as mock_shuffle:
            # Change the random shuffle to a deterministic list reverse
            mock_shuffle.side_effect = lambda x: x.reverse()

            query_results_actual = self.resolver.answer_query(query)
            self.assertSetEqual(set(query_results_expected),
                                set(query_results_actual))

        mock_fetch.assert_called_with(tool_properties_expected)


class AllResolverTestCase(ResolverTestCaseBase):

    def setUp(self):
        tool_fetcher_patch = mock.patch.object(
            tool_fetcher, 'ToolFetcher', autospec=True)
        self.addCleanup(tool_fetcher_patch.stop)
        tool_fetcher_patch.start()
        self.resolver = resolver.AllResolver()

    def testAnswerQueryWhenMatchingToolsExist(self):
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID

        mock_fetched_tools = [_createSliverTool(_TOOL_ID),
                              _createSliverTool(_TOOL_ID)]

        # AllResolver should not do any additional filtering on the tools it
        # fetched.
        query_results_expected = mock_fetched_tools

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        self.assertQueryResultMultiTool(query, mock_fetched_tools,
                                        query_results_expected,
                                        tool_properties_expected)

    def testAnswerQueryWhenMatchingToolsExistAndQuerySpecifiesAf(self):
        """Resolver should take into account address family when specified."""
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.tool_address_family = message.ADDRESS_FAMILY_IPv6

        mock_fetched_tools = [_createSliverTool(_TOOL_ID),
                              _createSliverTool(_TOOL_ID)]

        # AllResolver should not do any additional filtering on the tools it
        # fetched.
        query_results_expected = mock_fetched_tools

        # Make sure the resolver is fetching only tools with IPv6 interface
        # online that match the specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, address_family=message.ADDRESS_FAMILY_IPv6,
            status=message.STATUS_ONLINE)

        self.assertQueryResultMultiTool(query, mock_fetched_tools,
                                        query_results_expected,
                                        tool_properties_expected)

    def testAnswerQueryWhenNoToolsMatchToolId(self):
        tool_id = 'non_existent_tool'
        query = lookup_query.LookupQuery()
        query.tool_id = tool_id

        # Simulate no matching tools
        tool_fetcher.ToolFetcher().fetch.return_value = []

        query_results = self.resolver.answer_query(query)

        # Result should be None when there are no matches.
        self.assertIsNone(query_results)


class GeoResolverTestCase(ResolverTestCaseBase):

    def setUp(self):
        tool_fetcher_patch = mock.patch.object(
            tool_fetcher, 'ToolFetcher', autospec=True)
        self.addCleanup(tool_fetcher_patch.stop)
        tool_fetcher_patch.start()
        self.resolver = resolver.GeoResolver()

    def testAnswerQueryWhenSingleToolIsClosest(self):
        """When a single tool is closest, return that tool."""
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.latitude = 0.0
        query.longitude = 0.0

        close_tool = _createSliverTool(
            _TOOL_ID, site_id='abc01', latitude=1.0, longitude=1.0)
        far_tool = _createSliverTool(
            _TOOL_ID, site_id='cba01', latitude=5.0, longitude=5.0)

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        mock_fetched_tools = [close_tool, far_tool]
        self.assertQueryResultSingleTool(query, mock_fetched_tools, close_tool,
                                         tool_properties_expected)

    def testAnswerQueryWhenSingleToolIsClosestAndQuerySpecifiesAf(self):
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.latitude = 0.0
        query.longitude = 0.0
        query.tool_address_family = message.ADDRESS_FAMILY_IPv4

        close_tool = _createSliverTool(
            _TOOL_ID, site_id='abc01', latitude=1.0, longitude=1.0)
        far_tool = _createSliverTool(
            _TOOL_ID, site_id='cba01', latitude=5.0, longitude=5.0)

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, address_family=message.ADDRESS_FAMILY_IPv4,
            status=message.STATUS_ONLINE)

        mock_fetched_tools = [close_tool, far_tool]
        self.assertQueryResultSingleTool(query, mock_fetched_tools, close_tool,
                                         tool_properties_expected)

    def testAnswerQueryWhenMultipleToolsAreEquallyClose(self):
        """When multiple tools are equally closest, randomly select one."""
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.latitude = 0.0
        query.longitude = 0.0

        equidistant_tools = (
            _createSliverTool(_TOOL_ID, site_id='aaa01', latitude=1.0,
                              longitude=5.0),
            _createSliverTool(_TOOL_ID, site_id='bbb01', latitude=5.0,
                              longitude=1.0))

        mock_fetched_tools = [
            _createSliverTool(_TOOL_ID, site_id='ccc01', latitude=10.0,
                              longitude=10.0),
            _createSliverTool(_TOOL_ID, site_id='ddd01', latitude=20.0,
                              longitude=20.0)]
        mock_fetched_tools.extend(equidistant_tools)

        query_results_expected = [equidistant_tools[-1]]

        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        self.assertQueryResultWithRandomShuffle(
            query, mock_fetched_tools, query_results_expected,
            tool_properties_expected)

    def testAnswerQueryWhenNoToolsMatchToolId(self):
        tool_id = 'non_existent_tool'
        query = lookup_query.LookupQuery()
        query.tool_id = tool_id

        # Simulate no matching tools
        tool_fetcher.ToolFetcher().fetch.return_value = []

        # Result should be None when there are no matches.
        self.assertIsNone(self.resolver.answer_query(query))

    def testAnswerQueryReturnsRandomToolWhenQueryIsMissingLatLon(self):
        # TODO(mtlynch): This behavior is confusing because it is inconsistent
        # with the other resolvers that return None when required attributes are
        # missing from the query. Change so that all are consistent.
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID

        mock_fetched_tools = [
            _createSliverTool(
                _TOOL_ID, site_id='abc01', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='cba01', latitude=5.0, longitude=5.0)]

        # When lat/lon is missing, resolver performs no additional filtering
        # after fetch
        filtered_tools_expected = mock_fetched_tools

        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        self.assertQueryResultMultiToolWithRandomSample(
            query, mock_fetched_tools, filtered_tools_expected, 1,
            tool_properties_expected)


class GeoResolverWithOptionsTestCase(ResolverTestCaseBase):

    def setUp(self):
        tool_fetcher_patch = mock.patch.object(
            tool_fetcher, 'ToolFetcher', autospec=True)
        self.addCleanup(tool_fetcher_patch.stop)
        tool_fetcher_patch.start()
        self.resolver = resolver.GeoResolverWithOptions()
        # Allow full diff output on test failures
        self.maxDiff = None

    def testAnswerQueryWhenFourToolsAreEquallyClosest(self):
        """When exactly four tools tie for closest, return those four."""
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.latitude = 0.0
        query.longitude = 0.0

        mock_fetched_tools = [
            _createSliverTool(
                _TOOL_ID, site_id='abc01', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc02', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc03', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc04', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='cba01', latitude=5.0, longitude=5.0)
            ]
        # Result should be the four closest tools
        query_results_expected = mock_fetched_tools[:4]

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        self.assertQueryResultMultiTool(query, mock_fetched_tools,
                                        query_results_expected,
                                        tool_properties_expected)

    def testAnswerQueryWhenMoreThanFourToolsAreEquallyClosest(self):
        """When more than four tools tie for closest, randomly select four."""
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.latitude = 0.0
        query.longitude = 0.0

        mock_fetched_tools = [
            _createSliverTool(
                _TOOL_ID, site_id='abc01', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc02', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc03', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc04', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc05', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc06', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='cba01', latitude=5.0, longitude=5.0)
            ]
        # The mock shuffle reverses the list, so we expect items 2...6 in
        # reverse order.
        query_results_expected = mock_fetched_tools[-2:-6:-1]

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        self.assertQueryResultWithRandomShuffle(
            query, mock_fetched_tools, query_results_expected,
            tool_properties_expected)

    def testAnswerQueryWhenMoreThanFourToolsFromDifferentSitesAreEquallyClosest(
            self):
        """When more than four tools tie for closest, randomly select four."""
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.latitude = 0.0
        query.longitude = 0.0

        mock_fetched_tools = [
            _createSliverTool(
                _TOOL_ID, site_id='aaa01', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='bbb01', latitude=-1.0, longitude=-1.0),
            _createSliverTool(
                _TOOL_ID, site_id='ccc01', latitude=-1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='ddd01', latitude=1.0, longitude=-1.0),
            _createSliverTool(
                _TOOL_ID, site_id='eee01', latitude=-1.0, longitude=-1.0),
            _createSliverTool(
                _TOOL_ID, site_id='fff01', latitude=-1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='ggg01', latitude=5.0, longitude=5.0)
            ]
        # The mock shuffle reverses the list, so we expect items 2...6 in
        # reverse order.
        query_results_expected = mock_fetched_tools[-2:-6:-1]

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        self.assertQueryResultWithRandomShuffle(
            query, mock_fetched_tools, query_results_expected,
            tool_properties_expected)

    def testAnswerQueryWhenFewerThanFourToolsMatch(self):
        """When fewer than four tools match, return whatever matches."""
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.latitude = 0.0
        query.longitude = 0.0

        mock_fetched_tools = [
            _createSliverTool(
                _TOOL_ID, site_id='abc01', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc02', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='cba01', latitude=5.0, longitude=5.0)
            ]
        query_results_expected = mock_fetched_tools

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        self.assertQueryResultMultiTool(query, mock_fetched_tools,
                                        query_results_expected,
                                        tool_properties_expected)

    def testAnswerQueryWhenNoToolsMatchToolId(self):
        tool_id = 'non_existent_tool'
        query = lookup_query.LookupQuery()
        query.tool_id = tool_id

        # Simulate no matching tools
        tool_fetcher.ToolFetcher().fetch.return_value = []

        # Result should be None when there are no matches.
        self.assertIsNone(self.resolver.answer_query(query))

    def testAnswerQueryReturnsRandomSubsetWhenQueryIsMissingLatLon(self):
        """When lat/lon is missing, expect a random subset of tools."""
        # TODO(mtlynch): This behavior is confusing because it is inconsistent
        # with the other resolvers that return None when required attributes are
        # missing from the query. Change so that all are consistent.
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID

        mock_fetched_tools = [
            _createSliverTool(
                _TOOL_ID, site_id='abc01', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc02', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc03', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc04', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='cba01', latitude=5.0, longitude=5.0)]

        # When lat/lon is missing, resolver performs no additional filtering
        # after fetch
        filtered_tools_expected = mock_fetched_tools

        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        self.assertQueryResultMultiToolWithRandomSample(
            query, mock_fetched_tools, filtered_tools_expected, 4,
            tool_properties_expected)

    def testAnswerQueryReturnsRandomSubsetWhenQueryIsMissingLatLonLowCandidates(
        self):
        """When lat/lon is missing, expect a random subset of tools.

        If the number of matching candidates is lower than the number of tools
        requested, return all the matching candidates.
        """
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID

        mock_fetched_tools = [
            _createSliverTool(
                _TOOL_ID, site_id='abc01', latitude=1.0, longitude=1.0),
            _createSliverTool(
                _TOOL_ID, site_id='abc02', latitude=1.0, longitude=1.0)]
        # When lat/lon is missing, resolver performs no additional filtering
        # after fetch
        filtered_tools_expected = mock_fetched_tools

        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE)

        # Normally we expect a random sample of 4, but there are only 2
        # candidates in the set
        self.assertQueryResultMultiToolWithRandomSample(
            query, mock_fetched_tools, filtered_tools_expected, 2,
            tool_properties_expected)


class RandomResolverTestCase(ResolverTestCaseBase):

    def setUp(self):
        tool_fetcher_patch = mock.patch.object(
            tool_fetcher, 'ToolFetcher', autospec=True)
        self.addCleanup(tool_fetcher_patch.stop)
        tool_fetcher_patch.start()
        self.resolver = resolver.RandomResolver()

    def testAnswerQueryChoosesRandomlyAmongOnlineTools(self):
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.tool_address_family = message.ADDRESS_FAMILY_IPv6

        mock_fetched_tools = (
            _createSliverTool(_TOOL_ID, site_id='aaa01'),
            _createSliverTool(_TOOL_ID, site_id='bbb01'),
            _createSliverTool(_TOOL_ID, site_id='ccc01'),
            _createSliverTool(_TOOL_ID, site_id='ddd01'))

        # Random resolver performs no additional filtering after the fetch.
        filtered_tools_expected = mock_fetched_tools

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, address_family=message.ADDRESS_FAMILY_IPv6,
            status=message.STATUS_ONLINE)

        self.assertQueryResultSingleToolWithRandomChoice(
            query, mock_fetched_tools, filtered_tools_expected,
            tool_properties_expected)

    def testAnswerQueryWhenNoToolsMatchToolId(self):
        tool_id = 'non_existent_tool'
        query = lookup_query.LookupQuery()
        query.tool_id = tool_id

        # Simulate no matching tools
        tool_fetcher.ToolFetcher().fetch.return_value = []

        # Result should be None when there are no matches.
        self.assertIsNone(self.resolver.answer_query(query))


class MetroResolverTestCase(ResolverTestCaseBase):

    def setUp(self):
        tool_fetcher_patch = mock.patch.object(
            tool_fetcher, 'ToolFetcher', autospec=True)
        self.addCleanup(tool_fetcher_patch.stop)
        tool_fetcher_patch.start()
        self.resolver = resolver.MetroResolver()

    def testAnswerReturnsNoneWhenMetroIsNotSpecified(self):
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        # query omits country attribute

        candidate_tools = (_createSliverTool(_TOOL_ID),
                           _createSliverTool(_TOOL_ID))

        mock_fetch = tool_fetcher.ToolFetcher().fetch
        mock_fetch.return_value = candidate_tools
        query_results = self.resolver.answer_query(query)

        # Result should be None when there are no matches.
        self.assertIsNone(query_results)

    def testAnswerQueryChoosesRandomlyAmongToolsInMetro(self):
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.metro = 'aaa'
        query.tool_address_family = message.ADDRESS_FAMILY_IPv4

        mock_fetched_tools = (
            _createSliverTool(_TOOL_ID, site_id='aaa01'),
            _createSliverTool(_TOOL_ID, site_id='aaa02'),
            _createSliverTool(_TOOL_ID, site_id='aaa03'))

        filtered_tools_expected = mock_fetched_tools

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID in the specified metro.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE,
            address_family=message.ADDRESS_FAMILY_IPv4, metro=query.metro)

        self.assertQueryResultSingleToolWithRandomChoice(
            query, mock_fetched_tools, filtered_tools_expected,
            tool_properties_expected)


class CountryResolverTestCase(ResolverTestCaseBase):

    def setUp(self):
        tool_fetcher_patch = mock.patch.object(
            tool_fetcher, 'ToolFetcher', autospec=True)
        self.addCleanup(tool_fetcher_patch.stop)
        tool_fetcher_patch.start()
        self.resolver = resolver.CountryResolver()

    def testAnswerReturnsNoneWhenCountryIsNotSpecified(self):
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        # query omits country attribute

        candidate_tools = (_createSliverTool(_TOOL_ID),
                           _createSliverTool(_TOOL_ID))

        mock_fetch = tool_fetcher.ToolFetcher().fetch
        mock_fetch.return_value = candidate_tools
        query_results = self.resolver.answer_query(query)

        # Result should be None when there are no matches.
        self.assertIsNone(query_results)

    def testAnswerQueryChoosesRandomlyAmongToolsInCountry(self):
        country = 'valid_country'
        query = lookup_query.LookupQuery()
        query.tool_id = _TOOL_ID
        query.tool_address_family = message.ADDRESS_FAMILY_IPv4
        query.country = country

        mock_fetched_tools = (
            _createSliverTool(_TOOL_ID, site_id='aaa01'),
            _createSliverTool(_TOOL_ID, site_id='bbb01'),
            _createSliverTool(_TOOL_ID, site_id='ccc01'))

        filtered_tools_expected = mock_fetched_tools

        # Make sure the resolver is fetching only online tools that match the
        # specified tool ID in the specified country.
        tool_properties_expected = tool_fetcher.ToolProperties(
            tool_id=_TOOL_ID, status=message.STATUS_ONLINE,
            address_family=message.ADDRESS_FAMILY_IPv4, country=country)

        self.assertQueryResultSingleToolWithRandomChoice(
            query, mock_fetched_tools, filtered_tools_expected,
            tool_properties_expected)


class ResolverTestCase(unittest.TestCase):

    def testNewResolver(self):
        self.assertIsInstance(resolver.new_resolver(message.POLICY_GEO),
                              resolver.GeoResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_METRO),
                              resolver.MetroResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_RANDOM),
                              resolver.RandomResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_COUNTRY),
                              resolver.CountryResolver)
        self.assertIsInstance(resolver.new_resolver('unrecognized_policy'),
                              resolver.RandomResolver)


if __name__ == '__main__':
    unittest.main()
