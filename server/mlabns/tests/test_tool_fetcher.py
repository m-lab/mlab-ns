import unittest

from mlabns.db import model
from mlabns.db import tool_fetcher
from mlabns.util import message

from google.appengine.ext import db
from google.appengine.ext import testbed


class ToolFetcherDatastoreTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.fetcher = tool_fetcher.ToolFetcherDatastore()
        self.db_root = db.Model(key_name='root')

    def tearDown(self):
        self.testbed.deactivate()

    def assertSiteIdsEqual(self, site_ids_expected, tools_actual):
        site_ids_actual = [t.site_id for t in tools_actual]
        self.assertEqual(set(site_ids_expected), set(site_ids_actual))

    def verifyPropertiesReturnExpectedSiteIds(self, site_ids_expected,
                                              tool_properties):
        self.assertSiteIdsEqual(site_ids_expected,
                                self.fetcher.fetch(tool_properties))

    def insertSliverTool(self, tool_id, site_id=None, status_ipv4=None,
                         status_ipv6=None, latitude=None, longitude=None,
                         country=None):
        tool = model.SliverTool(parent=self.db_root.key())
        tool.tool_id = tool_id
        tool.site_id = site_id
        tool.status_ipv4 = status_ipv4
        tool.status_ipv6 = status_ipv6
        tool.latitude = latitude
        tool.longitude = longitude
        tool.country = country
        tool.put()

    def insertSite(self, site_id):
        site = model.Site(parent=self.db_root.key())
        site.site_id = site_id
        # Metro is always a 2-tuple where the first is the metro (first three
        # letters of the site ID) and the second is the site ID itself.
        site.metro = [site_id[:3], site_id]
        site.put()

    def initToolIdSiteGroup(self):
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertSliverTool(
            tool_id='mock_tool_b', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertSliverTool(
            tool_id='mock_tool_c', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_b', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc03', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_c', site_id='abc03', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)

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

    def init_status_site_group(self):
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc03', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='xyz01', country='CountryB',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)

    def testFetchToolsWithAtLeastOneOnlineInterface(self):
        self.init_status_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', status=message.STATUS_ONLINE)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02', 'xyz01'), tool_properties)

    def testFetchToolsWithAtLeastOneOfflineInterface(self):
        self.init_status_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', status=message.STATUS_OFFLINE)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc02', 'abc03', 'xyz01'), tool_properties)

    def testFetchToolsWithOnlineIpv4(self):
        self.init_status_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', status=message.STATUS_ONLINE,
            address_family=message.ADDRESS_FAMILY_IPv4)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02'), tool_properties)

    def testFetchToolsWithOnlineIpv6(self):
        self.init_status_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', status=message.STATUS_ONLINE,
            address_family=message.ADDRESS_FAMILY_IPv6)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'xyz01'), tool_properties)

    #TODO(mtlynch): Test when the AF is set, but with no status, should just ignore AF

    def init_country_site_group(self):
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='def01', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='xyz01', country='CountryB',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='zzz01', country='CountryC',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)

    def testFetchToolsInCountryA(self):
        self.init_country_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', country='CountryA')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02', 'def01'), tool_properties)

    def testFetchToolsInCountryB(self):
        self.init_country_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', country='CountryB')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('xyz01',), tool_properties)

    def testFetchToolsInNonExistentCountry(self):
        self.init_country_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', country='non_existent_country')
        self.verifyPropertiesReturnExpectedSiteIds([], tool_properties)

    def init_metro_site_group(self):
        self.insertSite(site_id='abc01')
        self.insertSite(site_id='abc02')
        self.insertSite(site_id='def01')
        self.insertSite(site_id='def02')
        self.insertSite(site_id='xyz01')

        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc01', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='abc02', country='CountryA',
            status_ipv4=message.STATUS_ONLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='def01', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='def02', country='CountryA',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)
        self.insertSliverTool(
            tool_id='mock_tool_a', site_id='xyz01', country='CountryB',
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_ONLINE)

    def testFetchToolsInMetroAbc(self):
        self.init_metro_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='abc')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('abc01', 'abc02'), tool_properties)

    def testFetchToolsInMetroXyz(self):
        self.init_metro_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='xyz')
        self.verifyPropertiesReturnExpectedSiteIds(
            ('xyz01',), tool_properties)

    def testFetchToolsInNonExistentMetro(self):
        self.init_metro_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='qqq')
        self.verifyPropertiesReturnExpectedSiteIds([], tool_properties)

    def testFetchToolsInMetroDefWithAtLeastOneOnlineInterface(self):
        self.init_metro_site_group()
        tool_properties = tool_fetcher.ToolProperties(
            tool_id='mock_tool_a', metro='def', status=message.STATUS_ONLINE)
        self.verifyPropertiesReturnExpectedSiteIds(
            ('def02',), tool_properties)


if __name__ == '__main__':
    unittest.main()
