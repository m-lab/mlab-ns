import unittest2

from google.appengine.api import memcache
from google.appengine.api import namespace_manager
from google.appengine.ext import db
from google.appengine.ext import testbed

from mlabns.util import constants
from mlabns.util import message
from mlabns.util import resolver


def _apply_namespace_bug_workaround():
  """Apply workaround for namespace collision.

  There is currently a bug that causes test code to apply changes to an
  inconsistent data store namespace. This is a workaround that forces the
  data store's namespace into a consistent state. This must be called after
  activating the testbed.
  """
  namespace_manager.get_namespace()

# Defined at top level, to avoid pickle error, when using memcache.
class SliverToolMockup:
    def __init__(self, status_ipv4, status_ipv6):
        self.status_ipv4 = status_ipv4
        self.status_ipv6 = status_ipv6


class SliverToolSiteMockup:
    def __init__(self, site_id, status_ipv4, status_ipv6):
        self.site_id = site_id
        self.status_ipv4 = status_ipv4
        self.status_ipv6 = status_ipv6


class SiteMockup:
    def __init__(self, site_id, metro):
        self.site_id = site_id
        self.metro = metro


class ResolverBaseTestCase(unittest2.TestCase):
    def testGetCandidates(self):

        class QueryMockup:
            pass

        class ResolverBaseMockup(resolver.ResolverBase):
            def _get_candidates(self, unused_arg, address_family):
                if address_family == message.ADDRESS_FAMILY_IPv6:
                    return ['valid_candidate']
                return []

        base_resolver = ResolverBaseMockup()

        # Case 1) List is not empty for the input address family.
        query = QueryMockup()
        query.address_family = message.ADDRESS_FAMILY_IPv6
        self.assertListEqual(['valid_candidate'],
                             base_resolver.get_candidates(query))

        # Case 2) List is empty for input address_family and there is no
        #         user-defined address family.
        query = QueryMockup()
        query.address_family = message.ADDRESS_FAMILY_IPv4
        query.user_defined_af = None
        self.assertListEqual(['valid_candidate'],
                             base_resolver.get_candidates(query))

        # Case 3) List is empty for input address_family and user-defined
        #         address family == input address family.
        query = QueryMockup()
        query.address_family = message.ADDRESS_FAMILY_IPv4
        query.user_defined_af = message.ADDRESS_FAMILY_IPv4
        self.assertEqual(len(base_resolver.get_candidates(query)), 0)

        # Case 4) List is empty for input address_family and user-defined
        #         address family != input address family.
        query = QueryMockup()
        query.address_family = message.ADDRESS_FAMILY_IPv4
        query.user_defined_af = message.ADDRESS_FAMILY_IPv6
        self.assertListEqual(['valid_candidate'],
                             base_resolver.get_candidates(query))

    def testGetCandidatesYesMemcache(self):

        # Set up memcache stub.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        _apply_namespace_bug_workaround()

        sliver_tool_list = [
            SliverToolMockup(message.STATUS_ONLINE, message.STATUS_OFFLINE),
            SliverToolMockup(message.STATUS_OFFLINE, message.STATUS_ONLINE),
            SliverToolMockup(message.STATUS_OFFLINE, message.STATUS_ONLINE),
            SliverToolMockup(message.STATUS_ONLINE, message.STATUS_ONLINE),
            SliverToolMockup(message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('valid_tool_id', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        base_resolver = resolver.ResolverBase()
        self.assertEqual(
            2, len(base_resolver._get_candidates(QueryMockup(),
                                                 message.ADDRESS_FAMILY_IPv4)))
        self.assertEqual(
            3, len(base_resolver._get_candidates(QueryMockup(),
                                                 message.ADDRESS_FAMILY_IPv6)))

        # Tear down stub.
        self.testbed.deactivate()

    def testGetCandidatesYesMemcacheButOffline(self):

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        class SliverTool(db.Model):
            tool_id = db.StringProperty()
            status_ipv4 = db.StringProperty()
            status_ipv6 = db.StringProperty()

        class TestEntityGroupRoot(db.Model):
            """Entity group root"""
            pass

        # Set up datastore and memcache stubs.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        _apply_namespace_bug_workaround()

        sliver_tool_list = [
            SliverToolMockup(message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('valid_tool_id', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        root = TestEntityGroupRoot(key_name='root')
        st1 = SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.status_ipv4 = message.STATUS_ONLINE
        st1.status_ipv6 = message.STATUS_ONLINE
        st1.put()

        base_resolver = resolver.ResolverBase()
        self.assertEqual(
            0, len(base_resolver._get_candidates(QueryMockup(),
                                                 message.ADDRESS_FAMILY_IPv4)))
        self.assertEqual(
            0, len(base_resolver._get_candidates(QueryMockup(),
                                                 message.ADDRESS_FAMILY_IPv6)))

        # Tear down stub.
        self.testbed.deactivate()

    def testGetCandidatesNoMemcacheYesDatastore(self):

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        class SliverTool(db.Model):
            tool_id = db.StringProperty()
            status_ipv4 = db.StringProperty()
            status_ipv6 = db.StringProperty()

        class TestEntityGroupRoot(db.Model):
            """Entity group root"""
            pass

        # Set up datastore and memcache stubs.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        _apply_namespace_bug_workaround()

        root = TestEntityGroupRoot(key_name='root')
        st1 = SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.status_ipv4 = message.STATUS_ONLINE
        st1.status_ipv6 = message.STATUS_ONLINE
        st1.put()
        st2 = SliverTool(parent=root.key())
        st2.tool_id = 'valid_tool_id'
        st2.status_ipv4 = message.STATUS_ONLINE
        st2.status_ipv6 = message.STATUS_OFFLINE
        st2.put()
        st3 = SliverTool(parent=root.key())
        st3.tool_id = 'valid_tool_id'
        st3.status_ipv4 = message.STATUS_OFFLINE
        st3.status_ipv6 = message.STATUS_ONLINE
        st3.put()
        st4 = SliverTool(parent=root.key())
        st4.tool_id = 'valid_tool_id'
        st4.status_ipv4 = message.STATUS_OFFLINE
        st4.status_ipv6 = message.STATUS_ONLINE
        st4.put()
        st5 = SliverTool(parent=root.key())
        st5.tool_id = 'valid_tool_id'
        st5.status_ipv4 = message.STATUS_OFFLINE
        st5.status_ipv6 = message.STATUS_OFFLINE
        st5.put()

        base_resolver = resolver.ResolverBase()
        self.assertEqual(
            2, len(base_resolver._get_candidates(QueryMockup(),
                                                 message.ADDRESS_FAMILY_IPv4)))
        self.assertEqual(
            3, len(base_resolver._get_candidates(QueryMockup(),
                                                 message.ADDRESS_FAMILY_IPv6)))

        # Tear down stub.
        self.testbed.deactivate()

    def testGetCandidatesNoMemcacheNoDatastore(self):

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        class SliverTool(db.Model):
            tool_id = db.StringProperty()
            status_ipv4 = db.StringProperty()
            status_ipv6 = db.StringProperty()

        class TestEntityGroupRoot(db.Model):
            """Entity group root"""
            pass

        # Set up datastore and memcache stubs.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        _apply_namespace_bug_workaround()

        sliver_tool_list = [
            SliverToolMockup(message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('tool_id2', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        root = TestEntityGroupRoot(key_name='root')
        st1 = SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.status_ipv4 = message.STATUS_OFFLINE
        st1.status_ipv6 = message.STATUS_OFFLINE
        st1.put()

        base_resolver = resolver.ResolverBase()
        self.assertEqual(
            0, len(base_resolver._get_candidates(QueryMockup(),
                                                 message.ADDRESS_FAMILY_IPv4)))
        self.assertEqual(
            0, len(base_resolver._get_candidates(QueryMockup(),
                                                 message.ADDRESS_FAMILY_IPv6)))

        # Tear down stub.
        self.testbed.deactivate()

    def testGetCandidatesFromSitesYesMemcache(self):

        # Set up memcache stub.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        _apply_namespace_bug_workaround()

        sliver_tool_list = [
            SliverToolSiteMockup(
                's1', message.STATUS_ONLINE, message.STATUS_OFFLINE),
            SliverToolSiteMockup(
                's1', message.STATUS_OFFLINE, message.STATUS_ONLINE),
            SliverToolSiteMockup(
                's1', message.STATUS_OFFLINE, message.STATUS_ONLINE),
            SliverToolSiteMockup(
                's2', message.STATUS_ONLINE, message.STATUS_ONLINE),
            SliverToolSiteMockup(
                's1', message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('valid_tool_id', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        base_resolver = resolver.ResolverBase()
        self.assertEqual(
            1, len(base_resolver._get_candidates_from_sites(
                QueryMockup(), message.ADDRESS_FAMILY_IPv4, ['s1'])))
        self.assertEqual(
            2, len(base_resolver._get_candidates_from_sites(
                QueryMockup(), message.ADDRESS_FAMILY_IPv6, ['s1'])))

        # Tear down stub.
        self.testbed.deactivate()

    def testGetCandidatesFromSitesYesMemcacheButOffline(self):

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        class SliverTool(db.Model):
            tool_id = db.StringProperty()
            site_id = db.StringProperty()
            status_ipv4 = db.StringProperty()
            status_ipv6 = db.StringProperty()

        class TestEntityGroupRoot(db.Model):
            """Entity group root"""
            pass

        # Set up datastore and memcache stubs.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        _apply_namespace_bug_workaround()

        sliver_tool_list = [
            SliverToolSiteMockup(
                's2', message.STATUS_ONLINE, message.STATUS_ONLINE),
            SliverToolSiteMockup(
                's1', message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('valid_tool_id', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        root = TestEntityGroupRoot(key_name='root')
        st1 = SliverTool(parent=root.key())
        st1.site_id = 's1'
        st1.tool_id = 'valid_tool_id'
        st1.status_ipv4 = message.STATUS_ONLINE
        st1.status_ipv6 = message.STATUS_ONLINE
        st1.put()

        base_resolver = resolver.ResolverBase()
        self.assertEqual(
            0, len(base_resolver._get_candidates_from_sites(
                QueryMockup(), message.ADDRESS_FAMILY_IPv4, ['s1'])))
        self.assertEqual(
            0, len(base_resolver._get_candidates_from_sites(
                QueryMockup(), message.ADDRESS_FAMILY_IPv6, ['s1'])))

        # Tear down stub.
        self.testbed.deactivate()

    def testGetCandidatesFromSitesNoMemcacheYesDatastore(self):

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        class SliverTool(db.Model):
            tool_id = db.StringProperty()
            site_id = db.StringProperty()
            status_ipv4 = db.StringProperty()
            status_ipv6 = db.StringProperty()

        class TestEntityGroupRoot(db.Model):
            """Entity group root"""
            pass

        # Set up datastore and memcache stubs.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        _apply_namespace_bug_workaround()

        root = TestEntityGroupRoot(key_name='root')
        st1 = SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.site_id = 's1'
        st1.status_ipv4 = message.STATUS_ONLINE
        st1.status_ipv6 = message.STATUS_ONLINE
        st1.put()
        st2 = SliverTool(parent=root.key())
        st2.tool_id = 'valid_tool_id'
        st2.site_id = 's1'
        st2.status_ipv4 = message.STATUS_ONLINE
        st2.status_ipv6 = message.STATUS_OFFLINE
        st2.put()
        st3 = SliverTool(parent=root.key())
        st3.tool_id = 'valid_tool_id'
        st3.site_id = 's1'
        st3.status_ipv4 = message.STATUS_OFFLINE
        st3.status_ipv6 = message.STATUS_ONLINE
        st3.put()
        st4 = SliverTool(parent=root.key())
        st4.tool_id = 'valid_tool_id'
        st4.site_id = 's2'
        st4.status_ipv4 = message.STATUS_OFFLINE
        st4.status_ipv6 = message.STATUS_ONLINE
        st4.put()
        st5 = SliverTool(parent=root.key())
        st5.tool_id = 'valid_tool_id'
        st5.site_id = 's1'
        st5.status_ipv4 = message.STATUS_OFFLINE
        st5.status_ipv6 = message.STATUS_OFFLINE
        st5.put()

        base_resolver = resolver.ResolverBase()
        self.assertEqual(
            2, len(base_resolver._get_candidates_from_sites(
                QueryMockup(), message.ADDRESS_FAMILY_IPv4, ['s1'])))
        self.assertEqual(
            2, len(base_resolver._get_candidates_from_sites(
                QueryMockup(), message.ADDRESS_FAMILY_IPv6, ['s1'])))

        # Tear down stub.
        self.testbed.deactivate()

    def testGetCandidatesFromSitesNoMemcacheNoDatastore(self):

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        class SliverTool(db.Model):
            tool_id = db.StringProperty()
            site_id = db.StringProperty()
            status_ipv4 = db.StringProperty()
            status_ipv6 = db.StringProperty()

        class TestEntityGroupRoot(db.Model):
            """Entity group root"""
            pass

        # Set up datastore and memcache stubs.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        _apply_namespace_bug_workaround()

        sliver_tool_list = [
            SliverToolSiteMockup(
                's1', message.STATUS_OFFLINE, message.STATUS_OFFLINE)]
        memcache.set('tool_id2', sliver_tool_list,
                     namespace=constants.MEMCACHE_NAMESPACE_TOOLS)

        root = TestEntityGroupRoot(key_name='root')
        st1 = SliverTool(parent=root.key())
        st1.tool_id = 'valid_tool_id'
        st1.site_id = 's1'
        st1.status_ipv4 = message.STATUS_OFFLINE
        st1.status_ipv6 = message.STATUS_OFFLINE
        st1.put()

        base_resolver = resolver.ResolverBase()
        self.assertEqual(
            0, len(base_resolver._get_candidates_from_sites(
                QueryMockup(), message.ADDRESS_FAMILY_IPv4, ['s1'])))
        self.assertEqual(
            0, len(base_resolver._get_candidates_from_sites(
                QueryMockup(), message.ADDRESS_FAMILY_IPv6, ['s1'])))

        # Tear down stub.
        self.testbed.deactivate()

    def testAnswerQueryEmptyResult(self):
        class QueryMockup:
            def __init__(self):
                self.tool_id = 'tool_id'

        class ResolverBaseMockup(resolver.ResolverBase):
            def get_candidates(self, unused_arg):
                return []

        base_resolver = ResolverBaseMockup()
        query = QueryMockup()
        self.assertIsNone(base_resolver.answer_query(query))

    def testAnswerQueryNonEmptyResult(self):
        class QueryMockup:
            def __init__(self):
                self.tool_id = 'tool_id'

        class ResolverBaseMockup(resolver.ResolverBase):
            def get_candidates(self, unused_arg):
                return ['valid_candidate']

        base_resolver = ResolverBaseMockup()
        query = QueryMockup()
        self.assertListEqual(['valid_candidate'],
                             base_resolver.get_candidates(query))


class GeoResolverTestCase(unittest2.TestCase):
    def testAnswerQueryNoCandidates(self):

        class QueryMockup:
            def __init__(self):
                self.tool_id = 'valid_tool_id'

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return []

        geo_resolver = GeoResolverMockup()
        self.assertIsNone(geo_resolver.answer_query(QueryMockup()))

    def testAnswerQueryNoLatLon(self):

        class QueryMockup:
            def __init__(self):
                self.latitude = None
                self.longitude = None

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return ['valid_candidate']

        geo_resolver = GeoResolverMockup()
        results = geo_resolver.answer_query(QueryMockup())
        self.assertEqual(1, len(results))
        self.assertEqual('valid_candidate', results[0])

    def testAnswerQueryAllCandidatesSameSite(self):

        class QueryMockup:
            def __init__(self):
                self.latitude = 0.0
                self.longitude = 0.0

        class SliverToolMockup:
            def __init__(self):
                self.site_id = 'valid_site_id'
                self.latitude = 2.0
                self.longitude = 1.0

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return [SliverToolMockup(), SliverToolMockup()]

        geo_resolver = GeoResolverMockup()
        results = geo_resolver.answer_query(QueryMockup())
        self.assertEqual(1, len(results))
        self.assertEqual(2.0, results[0].latitude)
        self.assertEqual(1.0, results[0].longitude)

    def testAnswerQueryAllCandidatesDifferentSitesOneClosest(self):

        class QueryMockup:
            def __init__(self):
                self.latitude = 0.0
                self.longitude = 0.0

        class SliverToolMockup:
            def __init__(self, site, lat, lon):
                self.site_id = site
                self.latitude = lat
                self.longitude = lon

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return [SliverToolMockup('a', 2.0, 1.0),
                        SliverToolMockup('b', 20.0, 34.9)]

        geo_resolver = GeoResolverMockup()
        results = geo_resolver.answer_query(QueryMockup())
        self.assertEqual(1, len(results))
        self.assertEqual(2.0, results[0].latitude)
        self.assertEqual(1.0, results[0].longitude)

    def testAnswerQueryAllCandidatesDifferentSitesMultipleClosest(self):

        class QueryMockup:
            def __init__(self):
                self.latitude = 0.0
                self.longitude = 0.0

        class SliverToolMockup:
            def __init__(self, site, lat, lon):
                self.site_id = site
                self.latitude = lat
                self.longitude = lon

        class GeoResolverMockup(resolver.GeoResolver):
            def get_candidates(self, unused_arg):
                return [SliverToolMockup('a', 2.0, 1.0),
                        SliverToolMockup('b', 20.0, 34.9),
                        SliverToolMockup('c', 2.0, 1.0)]

        geo_resolver = GeoResolverMockup()
        results = geo_resolver.answer_query(QueryMockup())
        self.assertEqual(1, len(results))
        self.assertEqual(2.0, results[0].latitude)
        self.assertEqual(1.0, results[0].longitude)


class CountryResolverTestCase(unittest2.TestCase):
    def testAnswerQueryNoUserDefinedCountry(self):

        class QueryMockup:
            def __init__(self):
                self.user_defined_country = None

        class CountryResolverMockup(resolver.CountryResolver):
            pass

        country_resolver = CountryResolverMockup()
        self.assertIsNone(country_resolver.answer_query(QueryMockup()))

    def testAnswerQueryNoCandidates(self):

        class QueryMockup:
            def __init__(self):
                self.user_defined_country = 'valid_country'
                self.tool_id = 'valid_tool_id'

        class CountryResolverMockup(resolver.CountryResolver):
            def get_candidates(self, unused_arg):
                return []

        country_resolver = CountryResolverMockup()
        self.assertIsNone(country_resolver.answer_query(QueryMockup()))

    def testAnswerQueryNoCandidatesInUserDefinedCountry(self):

        class QueryMockup:
            def __init__(self):
                self.user_defined_country = 'valid_country'
                self.tool_id = 'valid_tool_id'

        class SliverToolMockup:
            def __init__(self, country):
                self.country = country

        class CountryResolverMockup(resolver.CountryResolver):
            def get_candidates(self, unused_arg):
                return [SliverToolMockup('valid_country1'),
                        SliverToolMockup('valid_country2')]

        country_resolver = CountryResolverMockup()
        self.assertIsNone(country_resolver.answer_query(QueryMockup()))

    def testAnswerQueryCandidatesInUserDefinedCountry(self):

        class QueryMockup:
            def __init__(self):
                self.user_defined_country = 'valid_country'
                self.tool_id = 'valid_tool_id'

        class SliverToolMockup:
            def __init__(self, country):
                self.country = country

        class CountryResolverMockup(resolver.CountryResolver):
            def get_candidates(self, unused_arg):
                return [SliverToolMockup('valid_country'),
                        SliverToolMockup('valid_country2')]

        country_resolver = CountryResolverMockup()
        result = country_resolver.answer_query(QueryMockup())
        self.assertEqual(1, len(result))
        self.assertEqual('valid_country', result[0].country)


class MetroResolverTestCase(unittest2.TestCase):
    def testGetCandidatesNoSites(self):

        class QueryMockup:
            def __init__(self):
                self.metro = 'metro1'

        class Site(db.Model):
            site_id = db.StringProperty()
            metro = db.StringListProperty()

        class TestEntityGroupRoot(db.Model):
            """Entity group root"""
            pass

        # Set up datastore stub.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        _apply_namespace_bug_workaround()

        root = TestEntityGroupRoot(key_name='root')
        st1 = Site(parent=root.key())
        st1.site_id = 's1'
        st1.metro = ['metro2']
        st1.put()

        metro_resolver = resolver.MetroResolver()
        self.assertEqual(
            0, len(metro_resolver._get_candidates(QueryMockup(), 'unused_arg')))

        # Tear down stub.
        self.testbed.deactivate()

    def testGetCandidatesYesSites(self):

        class QueryMockup:
            def __init__(self):
                self.metro = 'metro1'

        class Site(db.Model):
            site_id = db.StringProperty()
            metro = db.StringListProperty(default=None)

        class TestEntityGroupRoot(db.Model):
            """Entity group root"""
            pass

        # Set up datastore stub.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        _apply_namespace_bug_workaround()

        root = TestEntityGroupRoot(key_name='root')
        st1 = Site(parent=root.key())
        st1.site_id = 's1'
        st1.metro = ['metro1']
        st1.put()
        st2 = Site(parent=root.key())
        st2.site_id = 's2'
        st2.metro = ['metro1', 'site1']
        st2.put()
        st3 = Site(parent=root.key())
        st3.site_id = 's3'
        st3.metro = ['metro2', 'site2']
        st3.put()

        class MetroResolverMockup(resolver.MetroResolver):
            def _get_candidates_from_sites(self, unused_arg1, unused_arg2,
                                           site_list):
                return site_list

        metro_resolver = MetroResolverMockup()
        self.assertEqual(
            2, len(metro_resolver._get_candidates(QueryMockup(), 'unused_arg')))

        # Tear down stub.
        self.testbed.deactivate()


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
