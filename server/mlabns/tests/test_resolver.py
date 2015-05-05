from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed

import mock
import unittest2

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import resolver


# We need to define our own class here instead of using the mock library
# because this object needs to be pickled and Python cannot pickle
# mock.Mock objects.
class MockSliverTool():

    def __init__(self, site_id=None, status_ipv4=None, status_ipv6=None,
                 latitude=None, longitude=None):
        self.site_id = site_id
        self.status_ipv4 = status_ipv4
        self.status_ipv6 = status_ipv6
        self.latitude = latitude
        self.longitude = longitude


class TestEntityGroupRoot(db.Model):
    """Entity group root"""
    pass


class ResolverBaseTestCase(unittest2.TestCase):

    def setUp(self):
        # Set up memcache stub.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def testGetCandidates(self):

        class ResolverBaseMockup(resolver.ResolverBase):
            def _get_candidates(self, unused_arg, address_family):
                if address_family == message.ADDRESS_FAMILY_IPv6:
                    return ['valid_candidate']
                return []

        base_resolver = ResolverBaseMockup()

        # Case 1) List is not empty for the input address family.
        query = mock.Mock(address_family=message.ADDRESS_FAMILY_IPv6)
        self.assertListEqual(['valid_candidate'],
                             base_resolver.get_candidates(query))

        # Case 2) List is empty for input address_family and there is no
        #         user-defined address family.
        query = mock.Mock(address_family=message.ADDRESS_FAMILY_IPv4,
                          user_defined_af=None)
        self.assertListEqual(['valid_candidate'],
                             base_resolver.get_candidates(query))

        # Case 3) List is empty for input address_family and user-defined
        #         address family == input address family.
        query = mock.Mock(address_family=message.ADDRESS_FAMILY_IPv4,
                          user_defined_af=message.ADDRESS_FAMILY_IPv4)
        self.assertEqual(len(base_resolver.get_candidates(query)), 0)

        # Case 4) List is empty for input address_family and user-defined
        #         address family != input address family.
        query = mock.Mock(address_family=message.ADDRESS_FAMILY_IPv4,
                          user_defined_af=message.ADDRESS_FAMILY_IPv6)
        self.assertListEqual(['valid_candidate'],
                             base_resolver.get_candidates(query))

    def testGetCandidatesYesMemcache(self):
        sliver_tool_list = [
            MockSliverTool(status_ipv4=message.STATUS_ONLINE,
                           status_ipv6=message.STATUS_OFFLINE),
            MockSliverTool(status_ipv4=message.STATUS_OFFLINE,
                           status_ipv6=message.STATUS_ONLINE),
            MockSliverTool(status_ipv4=message.STATUS_OFFLINE,
                           status_ipv6=message.STATUS_ONLINE),
            MockSliverTool(status_ipv4=message.STATUS_ONLINE,
                           status_ipv6=message.STATUS_ONLINE),
            MockSliverTool(status_ipv4=message.STATUS_OFFLINE,
                           status_ipv6=message.STATUS_OFFLINE)]
        memcache.set('valid_tool_id', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        base_resolver = resolver.ResolverBase()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertEqual(
            2, len(base_resolver._get_candidates(mock_query,
                                                 message.ADDRESS_FAMILY_IPv4)))
        self.assertEqual(
            3, len(base_resolver._get_candidates(mock_query,
                                                 message.ADDRESS_FAMILY_IPv6)))


    def testGetCandidatesYesMemcacheButOffline(self):
        sliver_tool_list = [
            MockSliverTool(status_ipv4=message.STATUS_OFFLINE,
                           status_ipv6=message.STATUS_OFFLINE)]
        memcache.set('valid_tool_id', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        root = TestEntityGroupRoot(key_name='root')
        st1 = model.SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.status_ipv4 = message.STATUS_ONLINE
        st1.status_ipv6 = message.STATUS_ONLINE
        st1.put()

        base_resolver = resolver.ResolverBase()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertEqual(
            0, len(base_resolver._get_candidates(mock_query,
                                                 message.ADDRESS_FAMILY_IPv4)))
        self.assertEqual(
            0, len(base_resolver._get_candidates(mock_query,
                                                 message.ADDRESS_FAMILY_IPv6)))

    def testGetCandidatesNoMemcacheYesDatastore(self):
        root = TestEntityGroupRoot(key_name='root')
        st1 = model.SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.status_ipv4 = message.STATUS_ONLINE
        st1.status_ipv6 = message.STATUS_ONLINE
        st1.put()
        st2 = model.SliverTool(parent=root.key())
        st2.tool_id = 'valid_tool_id'
        st2.status_ipv4 = message.STATUS_ONLINE
        st2.status_ipv6 = message.STATUS_OFFLINE
        st2.put()
        st3 = model.SliverTool(parent=root.key())
        st3.tool_id = 'valid_tool_id'
        st3.status_ipv4 = message.STATUS_OFFLINE
        st3.status_ipv6 = message.STATUS_ONLINE
        st3.put()
        st4 = model.SliverTool(parent=root.key())
        st4.tool_id = 'valid_tool_id'
        st4.status_ipv4 = message.STATUS_OFFLINE
        st4.status_ipv6 = message.STATUS_ONLINE
        st4.put()
        st5 = model.SliverTool(parent=root.key())
        st5.tool_id = 'valid_tool_id'
        st5.status_ipv4 = message.STATUS_OFFLINE
        st5.status_ipv6 = message.STATUS_OFFLINE
        st5.put()

        base_resolver = resolver.ResolverBase()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertEqual(
            2, len(base_resolver._get_candidates(mock_query,
                                                 message.ADDRESS_FAMILY_IPv4)))
        self.assertEqual(
            3, len(base_resolver._get_candidates(mock_query,
                                                 message.ADDRESS_FAMILY_IPv6)))

    def testGetCandidatesNoMemcacheNoDatastore(self):
        sliver_tool_list = [
            MockSliverTool(status_ipv4=message.STATUS_OFFLINE,
                           status_ipv6=message.STATUS_OFFLINE)]
        memcache.set('tool_id2', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        root = TestEntityGroupRoot(key_name='root')
        st1 = model.SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.status_ipv4 = message.STATUS_OFFLINE
        st1.status_ipv6 = message.STATUS_OFFLINE
        st1.put()

        base_resolver = resolver.ResolverBase()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertEqual(
            0, len(base_resolver._get_candidates(mock_query,
                                                 message.ADDRESS_FAMILY_IPv4)))
        self.assertEqual(
            0, len(base_resolver._get_candidates(mock_query,
                                                 message.ADDRESS_FAMILY_IPv6)))

    def testGetCandidatesFromSitesYesMemcache(self):
        sliver_tool_list = [
            MockSliverTool(
                's1', message.STATUS_ONLINE, message.STATUS_OFFLINE),
            MockSliverTool(
                's1', message.STATUS_OFFLINE, message.STATUS_ONLINE),
            MockSliverTool(
                's1', message.STATUS_OFFLINE, message.STATUS_ONLINE),
            MockSliverTool(
                's2', message.STATUS_ONLINE, message.STATUS_ONLINE),
            MockSliverTool(
                's1', message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('valid_tool_id', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        base_resolver = resolver.ResolverBase()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertEqual(
            1, len(base_resolver._get_candidates_from_sites(
                mock_query, message.ADDRESS_FAMILY_IPv4, ['s1'])))
        self.assertEqual(
            2, len(base_resolver._get_candidates_from_sites(
                mock_query, message.ADDRESS_FAMILY_IPv6, ['s1'])))

    def testGetCandidatesFromSitesYesMemcacheButOffline(self):
        sliver_tool_list = [
            MockSliverTool(
                's2', message.STATUS_ONLINE, message.STATUS_ONLINE),
            MockSliverTool(
                's1', message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('valid_tool_id', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        root = TestEntityGroupRoot(key_name='root')
        st1 = model.SliverTool(parent=root.key())
        st1.site_id = 's1'
        st1.tool_id = 'valid_tool_id'
        st1.status_ipv4 = message.STATUS_ONLINE
        st1.status_ipv6 = message.STATUS_ONLINE
        st1.put()

        base_resolver = resolver.ResolverBase()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertEqual(
            0, len(base_resolver._get_candidates_from_sites(
                mock_query, message.ADDRESS_FAMILY_IPv4, ['s1'])))
        self.assertEqual(
            0, len(base_resolver._get_candidates_from_sites(
                mock_query, message.ADDRESS_FAMILY_IPv6, ['s1'])))

    def testGetCandidatesFromSitesNoMemcacheYesDatastore(self):
        root = TestEntityGroupRoot(key_name='root')
        st1 = model.SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.site_id = 's1'
        st1.status_ipv4 = message.STATUS_ONLINE
        st1.status_ipv6 = message.STATUS_ONLINE
        st1.put()
        st2 = model.SliverTool(parent=root.key())
        st2.tool_id = 'valid_tool_id'
        st2.site_id = 's1'
        st2.status_ipv4 = message.STATUS_ONLINE
        st2.status_ipv6 = message.STATUS_OFFLINE
        st2.put()
        st3 = model.SliverTool(parent=root.key())
        st3.tool_id = 'valid_tool_id'
        st3.site_id = 's1'
        st3.status_ipv4 = message.STATUS_OFFLINE
        st3.status_ipv6 = message.STATUS_ONLINE
        st3.put()
        st4 = model.SliverTool(parent=root.key())
        st4.tool_id = 'valid_tool_id'
        st4.site_id = 's2'
        st4.status_ipv4 = message.STATUS_OFFLINE
        st4.status_ipv6 = message.STATUS_ONLINE
        st4.put()
        st5 = model.SliverTool(parent=root.key())
        st5.tool_id = 'valid_tool_id'
        st5.site_id = 's1'
        st5.status_ipv4 = message.STATUS_OFFLINE
        st5.status_ipv6 = message.STATUS_OFFLINE
        st5.put()

        base_resolver = resolver.ResolverBase()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertEqual(
            2, len(base_resolver._get_candidates_from_sites(
                mock_query, message.ADDRESS_FAMILY_IPv4, ['s1'])))
        self.assertEqual(
            2, len(base_resolver._get_candidates_from_sites(
                mock_query, message.ADDRESS_FAMILY_IPv6, ['s1'])))

    def testGetCandidatesFromSitesNoMemcacheNoDatastore(self):
        sliver_tool_list = [
            MockSliverTool(
                's1', message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('tool_id2', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        root = TestEntityGroupRoot(key_name='root')
        st1 = model.SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.site_id = 's1'
        st1.status_ipv4 = message.STATUS_OFFLINE
        st1.status_ipv6 = message.STATUS_OFFLINE
        st1.put()

        base_resolver = resolver.ResolverBase()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertEqual(
            0, len(base_resolver._get_candidates_from_sites(
                mock_query, message.ADDRESS_FAMILY_IPv4, ['s1'])))
        self.assertEqual(
            0, len(base_resolver._get_candidates_from_sites(
                mock_query, message.ADDRESS_FAMILY_IPv6, ['s1'])))

    def testAnswerQueryEmptyResult(self):
        class ResolverBaseMockup(resolver.ResolverBase):
            def get_candidates(self, unused_arg):
                return []

        base_resolver = ResolverBaseMockup()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertIsNone(base_resolver.answer_query(mock_query))

    def testAnswerQueryNonEmptyResult(self):
        class ResolverBaseMockup(resolver.ResolverBase):
            def get_candidates(self, unused_arg):
                return ['valid_candidate']

        base_resolver = ResolverBaseMockup()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertListEqual(['valid_candidate'],
                             base_resolver.get_candidates(mock_query))


class GeoResolverTestCase(unittest2.TestCase):

    def testAnswerQueryNoCandidates(self):

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return []

        geo_resolver = GeoResolverMockup()
        mock_query = mock.Mock(tool_id='valid_tool_id')
        self.assertIsNone(geo_resolver.answer_query(mock_query))

    def testAnswerQueryNoLatLon(self):

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return ['valid_candidate']

        geo_resolver = GeoResolverMockup()
        mock_query = mock.Mock(latitude=None, longitude=None)
        results = geo_resolver.answer_query(mock_query)
        self.assertEqual(1, len(results))
        self.assertEqual('valid_candidate', results[0])

    def testAnswerQueryAllCandidatesSameSite(self):

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                mock_tool = mock.Mock(site_id='valid_site_id', latitude=2.0,
                                      longitude=1.0)
                return [mock_tool, mock_tool]

        geo_resolver = GeoResolverMockup()
        mock_query = mock.Mock(latitude=0.0, longitude=0.0)
        results = geo_resolver.answer_query(mock_query)
        self.assertEqual(1, len(results))
        self.assertEqual(2.0, results[0].latitude)
        self.assertEqual(1.0, results[0].longitude)

    def testAnswerQueryAllCandidatesDifferentSitesOneClosest(self):

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return [mock.Mock(site_id='a', latitude=2.0, longitude=1.0),
                        mock.Mock(site_id='b', latitude=20.0, longitude=34.9)]

        geo_resolver = GeoResolverMockup()
        mock_query = mock.Mock(latitude=0.0, longitude=0.0)
        results = geo_resolver.answer_query(mock_query)
        self.assertEqual(1, len(results))
        self.assertEqual(2.0, results[0].latitude)
        self.assertEqual(1.0, results[0].longitude)

    def testAnswerQueryAllCandidatesDifferentSitesMultipleClosest(self):

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return [mock.Mock(site_id='a', latitude=2.0, longitude=1.0),
                        mock.Mock(site_id='b', latitude=20.0,longitude=34.9),
                        mock.Mock(site_id='c', latitude=2.0, longitude=1.0)]

        geo_resolver = GeoResolverMockup()
        mock_query = mock.Mock(latitude=0.0, longitude=0.0)
        results = geo_resolver.answer_query(mock_query)
        self.assertEqual(1, len(results))
        self.assertEqual(2.0, results[0].latitude)
        self.assertEqual(1.0, results[0].longitude)


class CountryResolverTestCase(unittest2.TestCase):

    def testAnswerQueryNoUserDefinedCountry(self):
        country_resolver = resolver.CountryResolver()
        mock_query = mock.Mock(user_defined_country=None)
        self.assertIsNone(country_resolver.answer_query(mock_query))

    def testAnswerQueryNoCandidates(self):

        class CountryResolverMockup(resolver.CountryResolver):
            def get_candidates(self, unused_arg):
                return []

        country_resolver = CountryResolverMockup()
        mock_query = mock.Mock(tool_id='valid_tool_id',
                               user_defined_country='valid_country')
        self.assertIsNone(country_resolver.answer_query(mock_query))

    def testAnswerQueryNoCandidatesInUserDefinedCountry(self):

        class CountryResolverMockup(resolver.CountryResolver):
            def get_candidates(self, unused_arg):
                return [mock.Mock(country='valid_country1'),
                        mock.Mock(country='valid_country2')]

        country_resolver = CountryResolverMockup()
        mock_query = mock.Mock(tool_id='valid_tool_id',
                               user_defined_country='valid_country')
        self.assertIsNone(country_resolver.answer_query(mock_query))

    def testAnswerQueryCandidatesInUserDefinedCountry(self):

        class CountryResolverMockup(resolver.CountryResolver):
            def get_candidates(self, unused_arg):
                return [mock.Mock(country='valid_country'),
                        mock.Mock(country='valid_country2')]

        country_resolver = CountryResolverMockup()
        mock_query = mock.Mock(tool_id='valid_tool_id',
                               user_defined_country='valid_country')
        result = country_resolver.answer_query(mock_query)
        self.assertEqual(1, len(result))
        self.assertEqual('valid_country', result[0].country)


class MetroResolverTestCase(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def testGetCandidatesNoSites(self):
        root = TestEntityGroupRoot(key_name='root')
        st1 = model.Site(parent=root.key())
        st1.site_id = 's1'
        st1.metro = ['metro2']
        st1.put()

        metro_resolver = resolver.MetroResolver()
        mock_query = mock.Mock(metro='metro1')
        self.assertEqual(
            0, len(metro_resolver._get_candidates(mock_query, 'unused_arg')))

    def testGetCandidatesYesSites(self):

        class MetroResolverMockup(resolver.MetroResolver):
            def _get_candidates_from_sites(self, unused_arg1, unused_arg2,
                                           site_list):
                return site_list

        root = TestEntityGroupRoot(key_name='root')
        st1 = model.Site(parent=root.key())
        st1.site_id = 's1'
        st1.metro = ['metro1']
        st1.put()
        st2 = model.Site(parent=root.key())
        st2.site_id = 's2'
        st2.metro = ['metro1', 'site1']
        st2.put()
        st3 = model.Site(parent=root.key())
        st3.site_id = 's3'
        st3.metro = ['metro2', 'site2']
        st3.put()

        metro_resolver = MetroResolverMockup()
        mock_query = mock.Mock(metro='metro1')
        self.assertEqual(
            2, len(metro_resolver._get_candidates(mock_query, 'unused_arg')))


class ResolverTestCase(unittest2.TestCase):
    def testNewResolver(self):
        self.assertIsInstance(resolver.new_resolver(message.POLICY_GEO),
                              resolver.GeoResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_METRO),
                              resolver.MetroResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_RANDOM),
                              resolver.RandomResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_COUNTRY),
                              resolver.CountryResolver)
        self.assertIsInstance(resolver.new_resolver('another_policy'),
                              resolver.RandomResolver)


if __name__ == '__main__':
    unittest2.main()
