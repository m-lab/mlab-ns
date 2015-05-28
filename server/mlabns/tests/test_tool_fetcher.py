import collections
import unittest

import mock

from mlabns.db import model
from mlabns.db import tool_fetcher
from mlabns.util import constants
from mlabns.util import message

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed


class ToolFetcherTestCase(unittest.TestCase):

    def setUp(self):
        tool_fetcher_datastore_patch = mock.patch.object(
                tool_fetcher, 'ToolFetcherDatastore', autospec=True)
        self.addCleanup(tool_fetcher_datastore_patch.stop)
        tool_fetcher_datastore_patch.start()

        tool_fetcher_memcache_patch = mock.patch.object(
                tool_fetcher, 'ToolFetcherMemcache', autospec=True)
        self.addCleanup(tool_fetcher_memcache_patch.stop)
        tool_fetcher_memcache_patch.start()

        self.fetcher = tool_fetcher.ToolFetcher()

    def testFetchDoesNotHitDatastoreIfMemcacheHasRequiredData(self):
        # The mock response is just ints here for simplicity, though the real
        # function returns SliverTool objects.
        mock_memcache_response = [1, 2, 3]
        tool_fetcher.ToolFetcherMemcache().fetch.return_value = (
                mock_memcache_response)
        tool_properties = tool_fetcher.ToolProperties(tool_id='mock_tool_a')
        fetcher_results_actual = self.fetcher.fetch(tool_properties)
        self.assertSequenceEqual(mock_memcache_response, fetcher_results_actual)

        # Verify that we did not attempt to read from the Datastore
        self.assertFalse(tool_fetcher.ToolFetcherDatastore().fetch.called)

    def testFetchFailsOverToDatastoreWhenDataIsNotInMemcache(self):
        tool_fetcher.ToolFetcherMemcache().fetch.return_value = []
        # The mock response is just ints here for simplicity, though the real
        # function returns SliverTool objects.
        mock_datastore_response = [4, 5, 6]
        tool_fetcher.ToolFetcherDatastore().fetch.return_value = (
                mock_datastore_response)
        tool_properties = tool_fetcher.ToolProperties(tool_id='mock_tool_a')
        fetcher_results_actual = self.fetcher.fetch(tool_properties)
        self.assertSequenceEqual(mock_datastore_response,
                                 fetcher_results_actual)


class ToolFetcherCommonTests(object):
    """Common tests that apply to both the Datastore and Memcache fetchers."""

    def createSliverTool(self, tool_id, site_id=None, status_ipv4=None,
                         status_ipv6=None, latitude=None, longitude=None,
                         country=None):
        tool = model.SliverTool()
        tool.tool_id = tool_id
        tool.site_id = site_id
        tool.status_ipv4 = status_ipv4
        tool.status_ipv6 = status_ipv6
        tool.latitude = latitude
        tool.longitude = longitude
        tool.country = country
        self.created_tools.append(tool)

    def insertCreatedTools(self):
        """Subclasses must implement this function."""
        pass

    def assertSiteIdsEqual(self, site_ids_expected, tools_actual):
        site_ids_actual = [t.site_id for t in tools_actual]
        self.assertEqual(set(site_ids_expected), set(site_ids_actual))

    def verifyPropertiesReturnExpectedSiteIds(self, site_ids_expected,
                                              tool_properties):
        self.assertSiteIdsEqual(site_ids_expected,
                                self.fetcher.fetch(tool_properties))

    def initToolIdSiteGroup(self):
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.createSliverTool(
            tool_id='mock_tool_b', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.createSliverTool(
            tool_id='mock_tool_c', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_b', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc03', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_c', site_id='abc03', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertCreatedTools()

    def testFetchToolA(self):
        self.initToolIdSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(tool_id='mock_tool_a')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02', 'abc03'), tool_properties)

    def testFetchToolB(self):
        self.initToolIdSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(tool_id='mock_tool_b')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02'), tool_properties)

    def testFetchToolC(self):
        self.initToolIdSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(tool_id='mock_tool_c')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc03'), tool_properties)

    def testFetchNonExistentTool(self):
        self.initToolIdSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(tool_id='no_exist_tool')
        self.verifyPropertiesReturnExpectedSiteIds([], tool_properties)

    def initStatusSiteGroup(self):
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc03', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='xyz01', country='CountryB',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertCreatedTools()

    def testFetchToolsWithAtLeastOneOnlineInterface(self):
        self.initStatusSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', status=message.STATUS_ONLINE)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02', 'xyz01'), tool_properties)

    def testFetchToolsWithAtLeastOneOfflineInterface(self):
        self.initStatusSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', status=message.STATUS_OFFLINE)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc02', 'abc03', 'xyz01'), tool_properties)

    def testFetchToolsWithOnlineIpv4(self):
        self.initStatusSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', status=message.STATUS_ONLINE,
            address_family=message.ADDRESS_FAMILY_IPv4)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02'), tool_properties)

    def testFetchToolsWithOnlineIpv6(self):
        self.initStatusSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', status=message.STATUS_ONLINE,
            address_family=message.ADDRESS_FAMILY_IPv6)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'xyz01'), tool_properties)

    def testFetchWhenNoAfIsSpecifiedButStatusIsOmittedIgnoreAf(self):
        self.initStatusSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', address_family=message.ADDRESS_FAMILY_IPv6)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02', 'abc03', 'xyz01'), tool_properties)

    def initCountrySiteGroup(self):
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='def01', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='xyz01', country='CountryB',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='zzz01', country='CountryC',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertCreatedTools()

    def testFetchToolsInCountryA(self):
        self.initCountrySiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', country='CountryA')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02', 'def01'), tool_properties)

    def testFetchToolsInCountryB(self):
        self.initCountrySiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', country='CountryB')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('xyz01',), tool_properties)

    def testFetchToolsInNonExistentCountry(self):
        self.initCountrySiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', country='non_existent_country')
        self.verifyPropertiesReturnExpectedSiteIds([], tool_properties)


class ToolFetcherMemcacheTestCase(unittest.TestCase, ToolFetcherCommonTests):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.fetcher = tool_fetcher.ToolFetcherMemcache()
        self.created_tools = []

    def tearDown(self):
        self.testbed.deactivate()

    def insertCreatedTools(self):
        tools_by_id = collections.defaultdict(lambda: [])
        for tool in self.created_tools:
            tools_by_id[tool.tool_id].append(tool)
        for tool_id, tool_list in tools_by_id.iteritems():
            memcache.set(tool_id, tool_list,
                         namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

    def testFetchAlwaysReturnsNoResultsWhenMetroIsSet(self):
        """Memcache fetcher has no knowledge of metros, so returns nothing."""
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='abc')
        self.verifyPropertiesReturnExpectedSiteIds([], tool_properties)


class ToolFetcherDatastoreTestCase(unittest.TestCase, ToolFetcherCommonTests):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.fetcher = tool_fetcher.ToolFetcherDatastore()
        self.db_root = db.Model(key_name='root')
        self.created_tools = []

    def tearDown(self):
        self.testbed.deactivate()

    def insertCreatedTools(self):
        for tool in self.created_tools:
            tool.parent = parent=self.db_root.key()
            tool.put()

    def insertSite(self, site_id):
        site = model.Site(parent=self.db_root.key())
        site.site_id = site_id
        # Metro is always a 2-tuple where the first is the metro (first three
        # letters of the site ID) and the second is the site ID itself.
        site.metro = [site_id[:3], site_id]
        site.put()

    def initMetroSiteGroup(self):
        self.insertSite(site_id='abc01')
        self.insertSite(site_id='abc02')
        self.insertSite(site_id='def01')
        self.insertSite(site_id='def02')
        self.insertSite(site_id='xyz01')

        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='def01', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='def02', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.createSliverTool(
            tool_id='mock_tool_a', site_id='xyz01', country='CountryB',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertCreatedTools()

    def testFetchToolsInMetroAbc(self):
        self.initMetroSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='abc')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02'), tool_properties)

    def testFetchToolsInMetroXyz(self):
        self.initMetroSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='xyz')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('xyz01',), tool_properties)

    def testFetchToolsInNonExistentMetro(self):
        self.initMetroSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='qqq')
        self.verifyPropertiesReturnExpectedSiteIds([], tool_properties)

    def testFetchToolsInMetroDefWithAtLeastOneOnlineInterface(self):
        self.initMetroSiteGroup()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='def', status=message.STATUS_ONLINE)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('def02',), tool_properties)


if __name__ == '__main__':
    unittest.main()
